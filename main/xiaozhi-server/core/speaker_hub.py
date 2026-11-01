"""Speaker devices: extra players (e.g. a phone on a big PA speaker) that play
what the portal's selected Blimp plays, except video calls (those are peer to
peer). Not synced with the Blimp: each device plays audio as it arrives.

Each speaker keeps a websocket open at /xiaozhi/speaker/ on the conversation
port, authenticated like the conversation websocket (device-id = the speaker's
own id). The same id reconnecting replaces its old socket.

Server -> speaker: {"type": "welcome"},
                   {"type": "tts", "state": "start", "sample_rate"} then binary Opus
                   frames (the AI's voice, exactly as sent to the Blimp), then
                   {"type": "tts", "state": "stop", "interrupted"?},
                   {"type": "play", kind, id, title, mime, path, http_port} (fetch
                   http://<server>:<http_port><path>), {"type": "stop_audio" |
                   "pause_media" | "resume_media"}, {"type": "set_loop", loop},
                   {"type": "pong"}
Speaker -> server: {"type": "ping"} every 15 s
"""

import asyncio
import json

import websockets

from config.logger import setup_logging

TAG = __name__

CLOSE_REPLACED = 4002
IDLE_TIMEOUT = 45  # the speaker pings every 15 s
QUEUE_LIMIT = 400  # ~24 s of 60 ms frames; a speaker further behind than this is dropped
# Media commands the Blimp gets that speakers mirror
MEDIA_COMMANDS = ("play", "stop_audio", "pause_media", "resume_media", "set_loop")


class _Speaker:
    def __init__(self, websocket):
        self.websocket = websocket
        # One writer per speaker keeps the order and never blocks the Blimp's audio
        self.queue = asyncio.Queue(QUEUE_LIMIT)
        self.writer = asyncio.create_task(self._write())

    async def _write(self):
        try:
            while True:
                await self.websocket.send(await self.queue.get())
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            pass

    def put(self, data) -> bool:
        try:
            self.queue.put_nowait(data)
            return True
        except asyncio.QueueFull:
            return False


class SpeakerHub:
    def __init__(self, blimp_control):
        self.logger = setup_logging()
        self.blimp_control = blimp_control
        self.speakers = {}  # speaker id -> _Speaker

    def _mirrors(self, conn) -> bool:
        """Only the portal's selected Blimp is mirrored (any Blimp if none is selected)."""
        selected = self.blimp_control.selected
        return bool(self.speakers) and (selected is None or getattr(conn, "device_id", None) == selected)

    def _put(self, data):
        for speaker_id, speaker in list(self.speakers.items()):
            if not speaker.put(data):
                self.logger.bind(tag=TAG).warning(f"Speaker {speaker_id} is too far behind; disconnecting it")
                asyncio.create_task(speaker.websocket.close(1011, "too slow"))

    # ---------- what the Blimp gets ----------

    def audio(self, conn, opus_packet):
        if self._mirrors(conn):
            self._put(bytes(opus_packet))

    def tts_state(self, conn, state, interrupted=False):
        if not self._mirrors(conn):
            return
        message = {"type": "tts", "state": state}
        if state == "start":
            message["sample_rate"] = getattr(conn, "sample_rate", 24000)
        if interrupted:
            message["interrupted"] = True
        self._put(json.dumps(message))

    def media(self, message: dict):
        """A command sent to the selected Blimp; mirrored if it is about media."""
        if self.speakers and message.get("type") in MEDIA_COMMANDS:
            self._put(json.dumps(message))

    def media_status(self, old, new):
        """The selected Blimp's playback status changed on its own (clip ended,
        a conversation stopped it, ...): bring the speakers along."""
        if not self.speakers or old == new:
            return
        if new == "paused":
            self.media({"type": "pause_media"})
        elif new == "playing" and old == "paused":
            self.media({"type": "resume_media"})
        elif new != "playing" and old in ("playing", "paused"):
            self.media({"type": "stop_audio"})

    # ---------- a speaker's socket ----------

    async def handle(self, websocket, speaker_id: str):
        old = self.speakers.get(speaker_id)
        speaker = _Speaker(websocket)
        self.speakers[speaker_id] = speaker
        if old is not None:
            await old.websocket.close(CLOSE_REPLACED, "replaced by a new connection")
        self.logger.bind(tag=TAG).info(f"Speaker {speaker_id} online ({len(self.speakers)} connected)")
        speaker.put(json.dumps({"type": "welcome", "speaker_id": speaker_id}))
        try:
            while True:
                raw = await asyncio.wait_for(websocket.recv(), IDLE_TIMEOUT)
                if isinstance(raw, str) and '"ping"' in raw:
                    speaker.put(json.dumps({"type": "pong"}))
        except asyncio.TimeoutError:
            self.logger.bind(tag=TAG).warning(f"Speaker {speaker_id} went silent; closing")
        except websockets.ConnectionClosed:
            pass
        finally:
            speaker.writer.cancel()
            if self.speakers.get(speaker_id) is speaker:
                del self.speakers[speaker_id]
                self.logger.bind(tag=TAG).info(f"Speaker {speaker_id} offline")
            try:
                await websocket.close()
            except Exception:
                pass
