"""Beta: Qwen-Omni realtime mode.

When `omni_realtime.enabled` is on, one model (qwen3.8-omni-flash-realtime by default)
hears the Blimp's microphone and speaks the reply itself: no ASR, LLM or TTS. This
module is the bridge, one OmniRealtimeSession per Blimp connection:

    mic PCM 16 kHz --input_audio_buffer.append--> model (its own VAD ends the turn)
    model --response.audio.delta (PCM 24 kHz)--> resample --> opus --> tts_audio_queue

The reply goes through the normal playback path (sendAudioMessage), so pacing, the
volume boost, `tts start/stop`, subtitles and the speaker mirror work as with TTS.

Tools are the connection's usual ones (plugins + device MCP) as realtime function
calls. A camera photo is described by the configured VLLM and the description is the
tool result: images sent to the realtime model mid-turn are not seen.

The model keeps the whole conversation and re-bills it every turn, so the session
closes when a conversation ends (goodbye or idle) and the next wake starts fresh.
"""

import asyncio
import base64
import json
import os
import re
import time
import uuid
from typing import TYPE_CHECKING, Optional

import numpy as np
import websockets
from scipy.signal import resample_poly

from config.logger import setup_logging
from core.providers.tts.dto.dto import SentenceType
from core.utils import opus_encoder_utils

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
DEFAULT_MODEL = "qwen3.8-omni-flash-realtime"
DEFAULT_VOICE = "Tina"  # the server's own default (Chelsie) is rejected by 3.8
MODEL_RATE = 24000  # response.audio.delta is PCM16 mono at 24 kHz
TURN_DETECTION_TYPES = ("server_vad", "semantic_vad", "semantic_vad_ec")
# Numeric session fields: config key -> (session field, type). Unset = model default.
SAMPLING_FIELDS = {
    "temperature": float,
    "top_p": float,
    "top_k": int,
    "max_tokens": int,
    "presence_penalty": float,
    "repetition_penalty": float,
    "seed": int,
}
# Device tools left out: each call is a round trip before the reply starts. The
# avatar's expression is picked from the reply text instead (_pick_expression);
# set_expression stays for when the user asks for a face (OMNI_RULES).
SKIPPED_TOOL_WORDS = ("expression", "emotion")
EXPRESSION_TOOL_WORD = "set_expression"
DEFAULT_EXPRESSION_MODEL = "qwen3.6-flash"
EXPRESSION_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
TOOL_TIMEOUT = 30
# A photo's description (VLLM) is given up after this; the model then says so
PHOTO_TIMEOUT = 15
# A reply that gets no event from the model for this long is given up (the Blimp
# would otherwise stay "speaking" with its microphone closed)
STALL_TIMEOUT = 15
# Seconds for the model to start answering a wake greeting before the session is replaced
GREET_TIMEOUT = 4
SENTENCE_END = re.compile(r"(.+?[.!?。！？…]+[\"'”’)]*)(\s+|$)", re.S)

OMNI_RULES = """
You are talking out loud: the user hears your voice through the Blimp's small speaker.
- Speak naturally and briefly: one to three short sentences unless the user asks for more.
- Plain spoken language only: no markdown, lists, emoji, tags or stage directions.
- Reply in the language the user speaks unless they ask for another one.
- Whenever the user asks you to look at or see something, call camera_take_photo first, every time.
- Only when the user asks you to make a face or change your expression (e.g. "look happy", "make a sad face"),
  call self_set_expression with the closest expression, then answer briefly. Never call it on your own.
- When the user says goodbye, bye, see you, good night, that's all, or asks you to stop talking, you MUST call
  handle_exit_intent (with one short farewell) instead of answering in words: that ends the conversation.
""".strip()


def omni_config(config: dict) -> dict:
    return config.get("omni_realtime") or {}


def omni_enabled(config: dict) -> bool:
    return bool(omni_config(config).get("enabled"))


class OmniRealtimeSession:
    def __init__(self, conn: "ConnectionHandler"):
        self.conn = conn
        self.cfg = omni_config(conn.config)
        self.ws = None
        self.ready = asyncio.Event()
        self._connecting: Optional[asyncio.Task] = None
        self._reader: Optional[asyncio.Task] = None
        # Bumped by close(): a connect still under way when the session is closed
        # must not publish its socket (it raced close() and left a dead session)
        self._generation = 0
        # Set when the model starts a response (the greeting watchdog waits on it)
        self._response_started = asyncio.Event()
        self._pending_audio = []
        # Current reply turn (spans the tool calls inside it)
        self.turn_active = False
        self.turn_sentence_id = None
        self.transcript_buf = ""
        self.reply_text = ""
        self.pending_calls = []
        self.response_has_audio = False
        self.encoder = None
        self.out_rate = None
        self._vllm = None
        # Avatar expression: one per reply, from its first sentence
        self.last_user_text = ""
        self.face_turn_id = None
        self.face_set_by_tool = False  # the user asked for a face this turn: no automatic pick
        self._expression_client = None
        # Tool calls run in their own task, so the model's events (and its
        # keepalive) keep being read meanwhile; turn_gen tells a finished tool
        # whether its turn was interrupted in the meantime
        self.tools_running = False
        self.turn_gen = 0
        # Stall watchdog (see STALL_TIMEOUT)
        self.response_open = False
        self.last_event_at = time.monotonic()
        self._watchdog: Optional[asyncio.Task] = None
        # Diagnostics: audio sent to the model this session, and the current listen start
        self.sent_ms = 0
        self.listen_started_at = None
        self.listen_first_audio_logged = False
        # The user turn the model's VAD has open (speech started, not yet stopped)
        self.open_speech_item = None

    # ---------- connection ----------

    def _api_key(self) -> str:
        key = self.cfg.get("api_key")
        if key:
            return key
        # The Bailian key the rest of the server uses
        for module in ("LLM", "ASR", "TTS"):
            selected = self.conn.config.get("selected_module", {}).get(module)
            key = (self.conn.config.get(module, {}).get(selected) or {}).get("api_key")
            if key and not str(key).startswith("your"):
                return key
        raise RuntimeError("omni_realtime has no API key")

    def _alive(self) -> bool:
        """A usable session: a socket, marked ready, with its reader still running."""
        return (self.ws is not None and self.ready.is_set()
                and self._reader is not None and not self._reader.done())

    async def ensure_connected(self):
        if self._alive():
            return
        if self.ws is not None or self.ready.is_set():
            # Half-alive (reader gone, or ready without a socket): start over
            logger.bind(tag=TAG).warning("Omni realtime: session not usable; reconnecting")
            await self.close(reopen=False)
        for attempt in (1, 2):
            if self._connecting is None or self._connecting.done():
                self._connecting = asyncio.create_task(self._connect())
            try:
                await asyncio.shield(self._connecting)
                return
            except RuntimeError as e:
                # A connect that lost the race with close(): try once more
                if attempt == 2 or "while connecting" not in str(e):
                    raise

    async def _connect(self):
        model = self.cfg.get("model") or DEFAULT_MODEL
        started = time.monotonic()
        generation = self._generation
        self.ready.clear()
        # The socket stays private until the session is set up: publishing it early
        # let a concurrent close() take it, leaving a "ready" session without a
        # reader (2026-11-03: no greeting after a goodbye)
        ws = await websockets.connect(
            f"{URL}?model={model}",
            additional_headers={"Authorization": f"Bearer {self._api_key()}"},
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
        )
        try:
            first = json.loads(await asyncio.wait_for(ws.recv(), 10))
            if first.get("type") != "session.created":
                raise RuntimeError(f"unexpected first event: {first}")
            await ws.send(json.dumps({"type": "session.update", "session": self._session_config()}, ensure_ascii=False))
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
                if msg.get("type") == "session.updated":
                    break
                if msg.get("type") == "error":
                    raise RuntimeError(f"session.update rejected: {msg.get('error')}")
        except BaseException:
            await ws.close()
            raise
        if generation != self._generation:
            # close() ran meanwhile: this session isn't wanted any more
            await ws.close()
            raise RuntimeError("session closed while connecting")
        self.ws = ws
        self._reader = asyncio.create_task(self._read_loop(ws))
        if self._watchdog is None or self._watchdog.done():
            self._watchdog = asyncio.create_task(self._watch_stalls())
        self.ready.set()
        logger.bind(tag=TAG).info(
            f"Omni realtime session ready: {model}, voice {self.cfg.get('voice') or DEFAULT_VOICE}, "
            f"{time.monotonic() - started:.2f}s"
        )
        for frame in self._pending_audio:
            await self._append_audio(frame)
        self._pending_audio.clear()

    def _session_config(self) -> dict:
        cfg = self.cfg
        detection = cfg.get("turn_detection") or "server_vad"
        if detection not in TURN_DETECTION_TYPES:
            detection = "server_vad"
        turn = {"type": detection}
        if cfg.get("vad_threshold") is not None:
            turn["threshold"] = float(cfg["vad_threshold"])
        if cfg.get("silence_duration_ms") is not None:
            turn["silence_duration_ms"] = int(cfg["silence_duration_ms"])
        session = {
            "modalities": ["text", "audio"],
            "instructions": self._instructions(),
            "voice": cfg.get("voice") or DEFAULT_VOICE,
            "audio": {
                "input": {"format": {"type": "pcm", "sample_rate": 16000}},
                "output": {"format": {"type": "pcm", "sample_rate": MODEL_RATE},
                           "voice": cfg.get("voice") or DEFAULT_VOICE},
            },
            "input_audio_transcription": {"model": "qwen3-asr-flash-realtime"},
            "turn_detection": turn,
        }
        for key, cast in SAMPLING_FIELDS.items():
            if cfg.get(key) is not None:
                session[key] = cast(cfg[key])
        if cfg.get("enable_search"):
            # Search and tools cannot be combined
            session["enable_search"] = True
        elif self._uses_tools():
            tools = self._tools()
            if tools:
                session["tools"] = tools
        return session

    def _uses_tools(self) -> bool:
        return not self.cfg.get("enable_search") and bool(self.cfg.get("tools", True))

    def _instructions(self) -> str:
        conn = self.conn
        parts = [str(conn.config.get("prompt") or "").strip(), OMNI_RULES]
        extra = str(self.cfg.get("instructions") or "").strip()
        if extra:
            parts.append(extra)
        pm = getattr(conn, "prompt_manager", None)
        if pm is not None:
            try:
                now = pm.now()
                part_of_day = ("night" if now.hour < 5 else "morning" if now.hour < 12
                               else "afternoon" if now.hour < 18 else "evening" if now.hour < 22 else "night")
                context = [f"Local time where the user is: {now:%A %Y-%m-%d %H:%M} ({part_of_day})"]
                if pm.local_address:
                    context.append(f"Device location: {pm.local_address}")
                if pm.weather_info:
                    context.append(f"Weather: {pm.weather_info}")
                parts.append("[Context]\n" + "\n".join(context))
            except Exception as e:  # context is a nicety
                logger.bind(tag=TAG).debug(f"No prompt context: {e}")
        return "\n\n".join(p for p in parts if p)

    def _tools(self) -> list:
        handler = getattr(self.conn, "func_handler", None)
        if handler is None:
            return []
        tools = []
        for desc in handler.get_functions() or []:
            fn = desc.get("function", {})
            name = fn.get("name", "")
            lname = name.lower()
            if not name or (any(w in lname for w in SKIPPED_TOOL_WORDS) and EXPRESSION_TOOL_WORD not in lname):
                continue
            tools.append({"type": "function", "function": {
                "name": name,
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters") or {"type": "object", "properties": {}},
            }})
        return tools

    async def _send(self, event: dict):
        if self.ws is None:
            logger.bind(tag=TAG).warning(f"Omni realtime: no session; dropped {event.get('type')}")
            return
        await self.ws.send(json.dumps(event, ensure_ascii=False))

    async def close(self, reopen: bool = True):
        """End the model session (its context is gone). With reopen, a fresh one is
        opened in the background for the next conversation."""
        self._generation += 1
        ws, self.ws = self.ws, None
        self.ready.clear()
        self.sent_ms = 0
        self._pending_audio.clear()
        self.turn_active = False
        self.turn_gen += 1
        self.response_open = False
        self.pending_calls = []
        if self._reader and not self._reader.done():
            self._reader.cancel()
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
            logger.bind(tag=TAG).info("Omni realtime session closed")
        if reopen and not self.conn.stop_event.is_set():
            asyncio.create_task(self.prewarm())

    # ---------- input ----------

    async def send_audio(self, pcm16k: bytes):
        conn = self.conn
        # Without barge-in the Blimp's speaker would answer itself through its mic
        if conn.client_is_speaking and not conn.config.get("barge_in", False):
            return
        if not self.ready.is_set():
            self._pending_audio.append(pcm16k)
            del self._pending_audio[:-50]  # keep the last ~3 s
            try:
                await self.ensure_connected()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Omni realtime connect failed: {e}")
                await self.close(reopen=False)
            return
        await self._append_audio(pcm16k)

    def listen_started(self):
        """The Blimp opened its microphone (listen start)."""
        self.listen_started_at = time.monotonic()
        self.listen_first_audio_logged = False
        self.listen_levels = []  # mic level per 0.5 s for the first seconds (diagnostics)
        self._level_acc = []
        logger.bind(tag=TAG).info(f"Omni realtime: listening (model has {self.sent_ms} ms of audio so far)")

    async def _append_audio(self, pcm16k: bytes):
        self.sent_ms += len(pcm16k) // 32
        if self.listen_started_at is not None and not self.listen_first_audio_logged:
            self.listen_first_audio_logged = True
            logger.bind(tag=TAG).info(
                f"Omni realtime: first audio {time.monotonic() - self.listen_started_at:.2f}s after listen start "
                f"(audio position {self.sent_ms} ms)")
        self._track_level(pcm16k)
        try:
            await self._send({"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm16k).decode()})
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Omni realtime audio send failed: {e}")
            await self.close(reopen=False)

    LEVEL_SECONDS = 8

    def _track_level(self, pcm16k: bytes):
        """Diagnostics: after each listen start, log the mic level (dBFS) per 0.5 s for
        the first LEVEL_SECONDS, to tell a silent mic from speech the model's VAD missed."""
        levels = getattr(self, "listen_levels", None)
        if levels is None or len(levels) >= self.LEVEL_SECONDS * 2:
            return
        self._level_acc.append(pcm16k)
        if sum(len(b) for b in self._level_acc) < 16000:  # 0.5 s of 16 kHz 16-bit
            return
        samples = np.frombuffer(b"".join(self._level_acc), dtype=np.int16).astype(np.float32) / 32768
        self._level_acc = []
        rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
        levels.append(round(20 * np.log10(max(rms, 1e-5))))
        if len(levels) == self.LEVEL_SECONDS * 2:
            logger.bind(tag=TAG).info(
                f"Omni realtime: mic level after listen start, dBFS per 0.5 s: {' '.join(map(str, levels))}")

    async def send_text(self, text: str):
        """Typed input (portal, chat panel): a user message, then a reply."""
        await self.ensure_connected()
        await self._send({"type": "conversation.item.create", "item": {
            "type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}})
        await self._send({"type": "response.create"})

    async def prewarm(self):
        """Open the session ahead of the wake word, so the greeting starts sooner."""
        try:
            await self.ensure_connected()
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Omni realtime prewarm failed (will retry on use): {e}")
            await self.close(reopen=False)

    async def drop_pending_input(self):
        """Forget a user turn the model is still waiting on, and any reply under way.

        When the Blimp stops sending audio in the middle of speech (conversation ended,
        mic closed), the model's VAD never sees the speech end and waits for it; a
        response.create in that state (the wake greeting) is ignored and the Blimp
        stays silent. Seen 2026-11-03: wake 3 s after a goodbye, no greeting. Clearing
        the buffer and deleting the item don't release the VAD (tested), so such a
        session is replaced by a fresh one (~0.15 s); otherwise any leftover is cleared."""
        if self.ws is None or not self.ready.is_set():
            return
        if self.open_speech_item:
            logger.bind(tag=TAG).info(
                "Omni realtime: the model still waits for an unfinished user turn; starting a fresh session")
            self.open_speech_item = None
            await self.close(reopen=False)
            await self.ensure_connected()
            return
        try:
            await self._send({"type": "response.cancel"})  # "not active" errors are ignored
            await self._send({"type": "input_audio_buffer.clear"})
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Omni realtime: could not clear pending input: {e}")
        self.response_open = False

    async def greet(self):
        """Wake greeting in the model's own voice. If the model hasn't started
        answering after GREET_TIMEOUT, the session is replaced and asked again once."""
        for attempt in (1, 2):
            await self.ensure_connected()
            await self.drop_pending_input()
            self._response_started.clear()
            # Fresh time/weather and the device tools (they register after the session opened)
            await self._send({"type": "session.update", "session": {
                "instructions": self._instructions(), **({"tools": self._tools()} if self._uses_tools() else {})}})
            await self._send({"type": "response.create", "response": {"instructions": (
                "The user just woke you up with your wake word. Greet them in one short, warm "
                "sentence (vary it) and ask what they need. Any time-of-day greeting must match the "
                "local time in your context.")}})
            try:
                await asyncio.wait_for(self._response_started.wait(), GREET_TIMEOUT)
                return
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning(
                    f"Omni realtime: no greeting {GREET_TIMEOUT}s after asking (attempt {attempt}); "
                    "replacing the session")
                await self.close(reopen=False)
        raise RuntimeError("the model did not greet")

    async def cancel(self):
        """The client interrupted the reply."""
        if self.turn_active and self.ready.is_set():
            try:
                await self._send({"type": "response.cancel"})
            except Exception:
                pass
        self.turn_active = False
        self.turn_gen += 1
        self.pending_calls = []

    async def _watch_stalls(self):
        while not self.conn.stop_event.is_set():
            await asyncio.sleep(2)
            # A running tool (a photo being taken and described) isn't a stall
            waiting = (self.response_open or self.turn_active) and not self.tools_running
            if not waiting or time.monotonic() - self.last_event_at < STALL_TIMEOUT:
                continue
            logger.bind(tag=TAG).warning(
                f"Omni realtime: no event from the model for {STALL_TIMEOUT}s during a reply; giving it up")
            self.response_open = False
            self.pending_calls = []
            try:
                await self._send({"type": "response.cancel"})
            except Exception:
                pass
            if self.turn_active:
                self._end_turn()
            else:
                # Nothing was played yet: tell the Blimp the (empty) reply is over
                from core.handle.sendAudioHandle import send_tts_message
                await send_tts_message(self.conn, "stop")

    # ---------- output ----------

    async def _read_loop(self, ws):
        try:
            async for raw in ws:
                try:
                    await self._handle(json.loads(raw))
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Omni realtime event failed: {type(e).__name__}: {e}")
        except websockets.ConnectionClosed as e:
            logger.bind(tag=TAG).info(f"Omni realtime connection closed: {e}")
        finally:
            if self.ws is ws:
                self.ws = None
                self.ready.clear()
                if self.turn_active:
                    self._end_turn()

    async def _handle(self, msg: dict):
        conn = self.conn
        t = msg.get("type", "")
        self.last_event_at = time.monotonic()
        if t == "response.created":
            self.response_open = True
            self._response_started.set()
        # Diagnostics: OMNI_TRACE=1 logs every model event except the deltas
        if os.environ.get("OMNI_TRACE") and not t.endswith(".delta"):
            logger.bind(tag=TAG).info(f"Omni trace: {t} {json.dumps(msg, ensure_ascii=False)[:200]}")
        if t == "input_audio_buffer.speech_started":
            self.open_speech_item = msg.get("item_id")
        elif t == "input_audio_buffer.speech_stopped":
            self.open_speech_item = None
        if t == "input_audio_buffer.speech_stopped":
            logger.bind(tag=TAG).info(f"Omni realtime: speech stopped at {msg.get('audio_end_ms')} ms (sent {self.sent_ms} ms)")
        elif t == "conversation.item.input_audio_transcription.failed":
            logger.bind(tag=TAG).warning(f"Omni realtime transcription failed: {msg.get('error')}")
        if t == "input_audio_buffer.speech_started":
            since = f", {time.monotonic() - self.listen_started_at:.2f}s after listen start" if self.listen_started_at else ""
            logger.bind(tag=TAG).info(
                f"Omni realtime: speech started at {msg.get('audio_start_ms')} ms (sent {self.sent_ms} ms{since})")
            conn.last_activity_time = time.time() * 1000
            if self.turn_active and conn.config.get("barge_in", False):
                from core.handle.abortHandle import handleAbortMessage
                logger.bind(tag=TAG).info("Omni realtime: user interrupted the reply")
                self.turn_active = False
                self.turn_gen += 1
                self.pending_calls = []
                await handleAbortMessage(conn)
        elif t == "conversation.item.input_audio_transcription.completed":
            text = (msg.get("transcript") or "").strip()
            if text:
                logger.bind(tag=TAG).info(f"Recognized text: {text}")
                await conn.websocket.send(json.dumps({"type": "stt", "text": text, "session_id": conn.session_id}))
                self._remember("user", text)
                self.last_user_text = text
        elif t == "response.audio_transcript.delta":
            await self._begin_turn()
            self.transcript_buf += msg.get("delta", "")
            self.reply_text += msg.get("delta", "")
            self._queue_sentences(final=False)
        elif t == "response.audio.delta":
            await self._begin_turn()
            self.response_has_audio = True
            self._queue_audio(base64.b64decode(msg.get("delta", "")))
        elif t == "response.audio.done":
            if self.encoder is not None and self.turn_active:
                self.encoder.encode_pcm_to_opus_stream(b"", True, self._queue_opus)
        elif t == "response.function_call_arguments.done":
            self.pending_calls.append(msg)
        elif t == "response.done":
            await self._response_done(msg.get("response") or {})
        elif t == "error":
            err = msg.get("error") or {}
            # Cancelling with nothing in flight is harmless
            if err.get("code") != "response_cancel_not_active":
                logger.bind(tag=TAG).error(f"Omni realtime error: {err}")

    async def _begin_turn(self):
        conn = self.conn
        if self.turn_active:
            return
        self.turn_active = True
        self.transcript_buf = ""
        self.reply_text = ""
        conn.client_abort = False
        conn.sentence_id = uuid.uuid4().hex
        self.turn_sentence_id = conn.sentence_id
        conn.tts.tts_audio_first_sentence = True
        if self.encoder is None or self.out_rate != conn.sample_rate:
            self.out_rate = conn.sample_rate
            self.encoder = opus_encoder_utils.OpusEncoderUtils(
                sample_rate=self.out_rate, channels=1, frame_size_ms=60
            )
        else:
            self.encoder.reset_state()
        conn.client_is_speaking = True
        from core.handle.sendAudioHandle import send_tts_message
        await send_tts_message(conn, "start")

    def _queue_sentences(self, final: bool):
        """Subtitles: each finished sentence of the reply transcript is a sentence_start."""
        while True:
            m = SENTENCE_END.match(self.transcript_buf)
            if not m:
                break
            self._sentence(m.group(1).strip())
            self.transcript_buf = self.transcript_buf[m.end():]
        if final and self.transcript_buf.strip():
            self._sentence(self.transcript_buf.strip())
            self.transcript_buf = ""

    def _sentence(self, text: str):
        self._put((SentenceType.FIRST, None, text))
        # The reply's first sentence sets the avatar's expression
        if (self.face_turn_id != self.turn_sentence_id and self.cfg.get("expressions", True)
                and not self.face_set_by_tool):
            self.face_turn_id = self.turn_sentence_id
            asyncio.create_task(self._pick_expression(self.last_user_text, text, self.turn_sentence_id))

    async def _pick_expression(self, user_text: str, sentence: str, sentence_id: str):
        """A small text model reads the reply as it starts and picks the avatar's face
        (the realtime model speaks its text, so it cannot write face tags, and a tool
        call would delay the voice by a round trip)."""
        from core.utils.textUtils import EXPRESSIONS, EXPRESSION_NAMES, send_expression
        started = time.monotonic()
        try:
            if self._expression_client is None:
                import openai
                config = self.conn.config
                llm = config.get("LLM", {}).get(config.get("selected_module", {}).get("LLM"), {}) or {}
                self._expression_client = openai.AsyncOpenAI(
                    api_key=self._api_key(), base_url=llm.get("base_url") or EXPRESSION_BASE_URL, timeout=5)
            system = (
                "You pick the facial expression of a cute robot avatar as it speaks a reply. Expressions: "
                + "; ".join(f"{n} ({m})" for n, m in EXPRESSIONS)
                + ". Answer with exactly one expression name. Use None for plain or factual replies."
            )
            reply = await self._expression_client.chat.completions.create(
                model=self.cfg.get("expression_model") or DEFAULT_EXPRESSION_MODEL,
                max_tokens=6, temperature=0, extra_body={"enable_thinking": False},
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": f"User said: {user_text or '(nothing)'}\nRobot replies: {sentence}"}],
            )
            name = EXPRESSION_NAMES.get(re.sub(r"[^a-z]", "", (reply.choices[0].message.content or "").lower()))
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Omni realtime expression pick failed: {e}")
            return
        # Too late: the reply was interrupted or a new one started
        if name is None or sentence_id != self.conn.sentence_id or self.conn.client_abort:
            return
        logger.bind(tag=TAG).info(f"Omni realtime expression: {name} ({time.monotonic() - started:.2f}s)")
        if name != "None":
            await send_expression(self.conn, name)

    def _queue_audio(self, pcm24k: bytes):
        if not pcm24k or not self.turn_active:
            return
        if self.out_rate != MODEL_RATE:
            samples = np.frombuffer(pcm24k, dtype=np.int16).astype(np.float32)
            g = np.gcd(self.out_rate, MODEL_RATE)
            samples = resample_poly(samples, self.out_rate // g, MODEL_RATE // g)
            pcm24k = np.clip(samples, -32768, 32767).astype(np.int16).tobytes()
        self.encoder.encode_pcm_to_opus_stream(pcm24k, False, self._queue_opus)

    def _queue_opus(self, packet: bytes):
        self._put((SentenceType.MIDDLE, packet, None))

    def _put(self, item):
        sentence_type, audio, text = item
        self.conn.tts.tts_audio_queue.put((sentence_type, audio, text, self.turn_sentence_id))

    async def _response_done(self, response: dict):
        self.response_open = False
        status = response.get("status")
        usage = response.get("usage") or {}
        if usage:
            logger.bind(tag=TAG).info(
                f"Omni realtime response {status}: input {usage.get('input_tokens')}, "
                f"output {usage.get('output_tokens')} tokens"
            )
        calls, self.pending_calls = self.pending_calls, []
        if status == "cancelled":
            self.turn_active = False
            return
        if calls:
            # The turn goes on: the model speaks again after the tool results. Not
            # awaited here: this runs inside the read loop, and a slow tool (a photo
            # takes seconds) would stop the connection being read until it died.
            self.tools_running = True
            asyncio.create_task(self._finish_calls(calls, self.turn_gen))
            return
        if self.turn_active:
            self._end_turn()

    def _end_turn(self):
        self._queue_sentences(final=True)
        reply = self.reply_text.strip()
        if reply:
            logger.bind(tag=TAG).info(f"Omni realtime reply: {reply}")
            self._remember("assistant", reply)
        # LAST sends `tts stop` once the audio has played (and ends the session if asked)
        self._put((SentenceType.LAST, [], None))
        self.turn_active = False
        self.face_set_by_tool = False

    def _remember(self, role: str, text: str):
        """Keep the dialogue for memory summaries, like the normal pipeline."""
        try:
            from core.utils.dialogue import Message
            self.conn.dialogue.put(Message(role=role, content=text))
        except Exception:
            pass

    # ---------- tools ----------

    async def _finish_calls(self, calls: list, gen: int):
        try:
            outputs = [(call, await self._run_tool(call)) for call in calls]
            # The model expects an output for each call, even if the turn is over
            for call, output in outputs:
                await self._send({"type": "conversation.item.create", "item": {
                    "type": "function_call_output", "call_id": call.get("call_id"), "output": output}})
            if gen != self.turn_gen or self.ws is None:
                logger.bind(tag=TAG).info("Omni realtime: turn ended while a tool ran; no reply to it")
                return
            await self._send({"type": "response.create"})
        except Exception as e:
            logger.bind(tag=TAG).error(f"Omni realtime tool results failed: {type(e).__name__}: {e}")
            if self.turn_active and gen == self.turn_gen:
                self._end_turn()
        finally:
            self.tools_running = False
            self.last_event_at = time.monotonic()

    async def _run_tool(self, call: dict) -> str:
        from plugins_func.register import Action
        conn = self.conn
        name = call.get("name", "")
        args = call.get("arguments") or "{}"
        logger.bind(tag=TAG).info(f"Omni realtime tool call: {name}({args[:120]})")
        if EXPRESSION_TOOL_WORD in name.lower():
            self.face_set_by_tool = True
        try:
            result = await asyncio.wait_for(
                conn.func_handler.handle_llm_function_call(
                    conn, {"name": name, "arguments": args, "id": call.get("call_id")}
                ),
                TOOL_TIMEOUT,
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Omni realtime tool {name} failed: {e}")
            return f"The tool failed: {e}. Tell the user briefly."
        if result is None:
            return "Done."
        images = conn._take_pending_images()
        if images:
            try:
                question = json.loads(args).get("question") or "Describe what you see."
            except (json.JSONDecodeError, AttributeError):
                question = "Describe what you see."
            return await self._describe_photo(images[0][0], question)
        if result.action == Action.RESPONSE:
            text = result.response or result.result or ""
            if name == "handle_exit_intent":
                return f"Say exactly this farewell to the user and nothing else: {text}"
            return f"Tell the user: {text}" if text else "Done."
        return str(result.result or result.response or "Done.")

    async def _describe_photo(self, data_url: str, question: str) -> str:
        if self._vllm is None:
            from core.utils.vllm import create_instance
            config = self.conn.config
            name = config.get("selected_module", {}).get("VLLM")
            vcfg = config.get("VLLM", {}).get(name) or {}
            if not vcfg:
                return "A photo was taken, but no vision model is configured to read it."
            self._vllm = create_instance(vcfg.get("type", name), vcfg)
        b64 = data_url.split(",", 1)[-1]
        # Short: the description is waited on mid-reply, and the model retells it anyway
        question = f"{question} Answer in one or two short sentences, only what matters for that."
        started = time.monotonic()
        try:
            text = await asyncio.wait_for(asyncio.to_thread(self._vllm.response, question, b64), PHOTO_TIMEOUT)
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).warning(f"Omni realtime photo description timed out after {PHOTO_TIMEOUT}s")
            return "A photo was taken, but reading it took too long. Tell the user briefly and offer to try again."
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Omni realtime photo description failed: {type(e).__name__}: {e}")
            return "A photo was taken, but it could not be read. Tell the user briefly and offer to try again."
        logger.bind(tag=TAG).info(f"Omni realtime photo described in {time.monotonic() - started:.1f}s")
        return f"Photo taken just now. What the camera shows: {text}"
