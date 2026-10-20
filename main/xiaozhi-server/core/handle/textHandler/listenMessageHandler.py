import time
import uuid
import asyncio
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

from core.utils.dialogue import Message
from core.providers.asr.dto.dto import InterfaceType
from core.handle.receiveAudioHandle import startToChat
from core.handle.helloHandle import playWakeupResponse
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType


TAG = __name__


async def wait_for_tts(conn: "ConnectionHandler", timeout: float = 3) -> bool:
    start_time = time.time()
    while not conn.tts and time.time() - start_time < timeout:
        await asyncio.sleep(0.1)
    return bool(conn.tts)

class ListenTextMessageHandler(TextMessageHandler):
    """Listen message handler"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn: "ConnectionHandler", msg_json: Dict[str, Any]) -> None:
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).debug(
                f"Client listening mode: {conn.client_listen_mode}"
            )
        if msg_json["state"] == "start":
            # The device switches from playback back to recording mode; clear all audio states and buffers
            conn.reset_audio_states()
        elif msg_json["state"] == "stop":
            # Received stop but ASR is not initialized; skip processing
            if conn.asr is None:
                return

            conn.client_voice_stop = True
            if conn.asr.interface_type == InterfaceType.STREAM:
                # In streaming mode, send the end request
                asyncio.create_task(conn.asr._send_stop_request())
            else:
                # Non-streaming mode: trigger ASR recognition directly
                if len(conn.asr_audio) > 0:
                    asr_audio_task = conn.asr_audio.copy()
                    conn.reset_audio_states()

                    if len(asr_audio_task) > 0:
                        await conn.asr.handle_voice_stop(conn, asr_audio_task)
        elif msg_json["state"] == "detect":
            conn.client_have_voice = False
            conn.reset_audio_states()
            if "text" in msg_json:
                conn.last_activity_time = time.time() * 1000
                original_text = msg_json["text"]  # keep the original text
                filtered_len, filtered_text = remove_punctuation_and_length(
                    original_text
                )

                # Check whether this is a device call command [device_call]
                if original_text.startswith("[device_call]"):
                    # Extract the text after the tag
                    call_text = original_text[len("[device_call]"):].strip()
                    conn.logger.bind(tag=TAG).info(f"Received device call command: {call_text}")

                    # Mark as incoming call answering mode
                    conn.incoming_call = True

                    # Prepare to start a new session
                    conn.sentence_id = uuid.uuid4().hex

                    await send_stt_message(conn, call_text)

                    # Wait for TTS initialization, up to 3 seconds
                    start_time = time.time()
                    while time.time() - start_time < 3:
                        if conn.tts:
                            break
                        await asyncio.sleep(0.1)

                    if conn.tts:
                        conn.tts.store_tts_text(conn.sentence_id, call_text)
                        conn.tts.tts_text_queue.put(TTSMessageDTO(sentence_id=conn.sentence_id, sentence_type=SentenceType.FIRST, content_type=ContentType.ACTION))
                        conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=call_text)
                        conn.tts.tts_text_queue.put(TTSMessageDTO(sentence_id=conn.sentence_id, sentence_type=SentenceType.LAST, content_type=ContentType.ACTION))

                    # Add to the dialogue history so the model understands the context
                    conn.dialogue.put(Message(role="assistant", content=call_text))
                    return

                # Explicit wake event from a client with local wake-word detection:
                # no need to guess from the text (typed input uses the same message)
                if msg_json.get("wake") is True and not conn.need_bind:
                    await self._handle_wake_event(conn, original_text)
                    return

                # Check whether it is a wake word
                is_wakeup_words = filtered_text in conn.config.get("wakeup_words")
                # Whether wake word replies are enabled
                enable_greeting = conn.config.get("enable_greeting", True)

                if is_wakeup_words and not enable_greeting:
                    # Wake word with replies disabled: no response needed
                    await send_stt_message(conn, original_text)
                    await send_tts_message(conn, "stop", None)
                    conn.client_is_speaking = False
                elif is_wakeup_words:
                    conn.just_woken_up = True
                    # Report plain text data (reusing the ASR reporting feature, but without audio data)
                    enqueue_asr_report(conn, "Hey there", [])
                    await startToChat(conn, "Hey there")
                else:
                    conn.just_woken_up = True
                    # Report plain text data (reusing the ASR reporting feature, but without audio data)
                    enqueue_asr_report(conn, original_text, [])
                    # Otherwise the LLM needs to reply to the text content
                    await startToChat(conn, original_text)

    async def _handle_wake_event(self, conn: "ConnectionHandler", text: str) -> None:
        # wake_greeting: "cached" (pre-generated greeting in the current voice),
        # "none" (just listen), or "llm" (let the LLM greet)
        mode = conn.config.get("wake_greeting", "cached")
        conn.logger.bind(tag=TAG).info(f"Wake event: {text} (greeting: {mode})")
        if mode == "llm":
            conn.just_woken_up = True
            enqueue_asr_report(conn, text, [])
            await startToChat(conn, text)
            return
        if mode == "cached" and await wait_for_tts(conn):
            await playWakeupResponse(conn)
            return
        # "none", or no TTS available: just let the client start listening
        conn.just_woken_up = True
        await send_tts_message(conn, "stop", None)
        conn.client_is_speaking = False
