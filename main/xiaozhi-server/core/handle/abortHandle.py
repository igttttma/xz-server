import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
TAG = __name__


async def handleAbortMessage(conn: "ConnectionHandler"):
    conn.logger.bind(tag=TAG).info("Abort message received")
    # Set the abort state; this automatically aborts the LLM and TTS tasks
    conn.close_after_chat = False
    conn.end_session_after_chat = False
    conn.client_abort = True
    conn.clear_queues()
    # Abort the client speaking state; "interrupted" tells the client to drop the
    # reply audio it still has buffered (a normal stop lets it play out)
    await conn.websocket.send(
        json.dumps({"type": "tts", "state": "stop", "interrupted": True, "session_id": conn.session_id})
    )
    speakers = getattr(getattr(conn, "server", None), "speaker_hub", None)
    if speakers:
        speakers.tts_state(conn, "stop", interrupted=True)
    conn.clearSpeakStatus()
    conn.logger.bind(tag=TAG).info("Abort message received-end")
