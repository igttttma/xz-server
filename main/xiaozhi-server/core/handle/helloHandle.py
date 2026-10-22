import os
import time
import json
import hashlib
import uuid
import random
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.handle.sendAudioHandle import sendAudioMessage, send_tts_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tools.device_mcp import MCPClient, send_mcp_initialize_message

TAG = __name__

# Wake greetings: each is synthesized once per voice, then kept on disk
WAKE_GREETINGS = [
    "I'm here, go ahead.",
    "Yes? I'm listening.",
    "Hi! What can I do for you?",
    "I'm here, please tell me.",
    "Go ahead, I'm listening.",
    "Hey! What's up?",
    "How can I help you?",
    "I'm all ears.",
    "Yes, I'm here.",
    "What would you like to know?",
]
WAKE_GREETINGS_DIR = "data/wake_greetings"

# One preparation per voice at a time
_greeting_locks: dict = {}


async def handleHelloMessage(conn: "ConnectionHandler", msg_json):
    """Handle the hello message"""
    audio_params = msg_json.get("audio_params")
    if audio_params:
        format = audio_params.get("format")
        conn.logger.bind(tag=TAG).debug(f"Client audio format: {format}")
        conn.audio_format = format
        conn.welcome_msg["audio_params"] = audio_params
    features = msg_json.get("features")
    if features:
        conn.logger.bind(tag=TAG).debug(f"Client features: {features}")
        conn.features = features
        if features.get("mcp"):
            conn.logger.bind(tag=TAG).debug("Client supports MCP")
            conn.mcp_client = MCPClient()
        if features.get("aec"):
            conn.logger.bind(tag=TAG).debug("Client enabled server-side AEC")
            conn.client_aec = True

    await conn.websocket.send(json.dumps(conn.welcome_msg))

    # The device waits for the server hello before processing MCP messages.
    if features and features.get("mcp"):
        asyncio.create_task(send_mcp_initialize_message(conn))


async def checkWakeupWords(conn: "ConnectionHandler", text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    # Wait for TTS initialization, up to 3 seconds
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False

    if not enable_wakeup_words_response_cache:
        return False

    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    await playWakeupResponse(conn)
    return True


def _greeting_dir(conn: "ConnectionHandler") -> str:
    """Clips depend on the TTS model, voice and output sample rate"""
    key = f"{getattr(conn.tts, 'model', '')}|{getattr(conn.tts, 'voice', '')}|{conn.sample_rate}"
    return os.path.join(WAKE_GREETINGS_DIR, hashlib.md5(key.encode()).hexdigest())


async def _greeting_clip(conn: "ConnectionHandler", index: int) -> str | None:
    """Path of greeting `index` in the current voice, synthesizing it if missing"""
    path = os.path.join(_greeting_dir(conn), f"{index}.wav")
    if os.path.exists(path):
        return path
    opus_datas = await asyncio.to_thread(conn.tts.to_tts, WAKE_GREETINGS[index])
    if not opus_datas:
        conn.logger.bind(tag=TAG).warning(f"Wake greeting {index} synthesis failed")
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Write then rename, so a reader never gets a half-written clip
    with open(path + ".tmp", "wb") as f:
        f.write(opus_datas_to_wav_bytes(opus_datas, sample_rate=conn.sample_rate))
    os.replace(path + ".tmp", path)
    return path


async def prepareWakeGreetings(conn: "ConnectionHandler"):
    """Synthesize the greetings the current voice does not have yet"""
    if not conn.tts:
        return
    lock = _greeting_locks.setdefault(_greeting_dir(conn), asyncio.Lock())
    if lock.locked():
        return
    async with lock:
        for index in range(len(WAKE_GREETINGS)):
            try:
                await _greeting_clip(conn, index)
            except Exception as e:
                conn.logger.bind(tag=TAG).warning(f"Wake greeting {index} failed: {e}")
                return


async def playWakeupResponse(conn: "ConnectionHandler"):
    """Play a random pre-generated wake greeting in the current TTS voice."""
    conn.just_woken_up = True
    await send_tts_message(conn, "start")

    ready = [
        i for i in range(len(WAKE_GREETINGS))
        if os.path.exists(os.path.join(_greeting_dir(conn), f"{i}.wav"))
    ]
    index = random.choice(ready or range(len(WAKE_GREETINGS)))
    path = await _greeting_clip(conn, index)
    if not ready:
        # New voice: record the others for the next wakes
        asyncio.create_task(prepareWakeGreetings(conn))
    if not path:
        await send_tts_message(conn, "stop", None)
        return
    text = WAKE_GREETINGS[index]

    opus_packets = await audio_to_data(path, use_cache=False)
    conn.client_abort = False

    # Treat the wake greeting as a new session and generate a new sentence_id so the flow controller resets
    conn.sentence_id = str(uuid.uuid4().hex)

    conn.logger.bind(tag=TAG).info(f"Playing wake greeting: {text}")
    await sendAudioMessage(conn, SentenceType.FIRST, opus_packets, text)
    await sendAudioMessage(conn, SentenceType.LAST, [], None)

    conn.dialogue.put(Message(role="assistant", content=text))
