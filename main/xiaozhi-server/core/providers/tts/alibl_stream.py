import os
import uuid
import json
import time
import queue
import asyncio
import traceback
import websockets

from typing import Callable, Any
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils.opus_encoder_utils import OpusEncoderUtils
from core.utils.alibl_endpoint import build_ws_connect_options, resolve_ws_url
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    TTS_PARAM_CONFIG = [
        ("ttsVolume", "volume", 0, 100, 50, int),
        ("ttsRate", "rate", 0.5, 2.0, 1.0, lambda v: round(v, 1)),
        ("ttsPitch", "pitch", 0.5, 2.0, 1.0, lambda v: round(v, 1)),
    ]

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        self.interface_type = InterfaceType.DUAL_STREAM
        # Basic configuration
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("api_key is required for CosyVoice TTS")

        # WebSocket configuration
        self.ws_url = resolve_ws_url(config.get("ws_url"))
        self.ws_connect_options = build_ws_connect_options(self.tts_timeout)
        self.ws = None
        self._monitor_task = None
        self.activate_session = False
        self.last_active_time = None
        # Task lifecycle per the CosyVoice WebSocket API: one task at a time per
        # connection, each with a fresh task_id; continue-task only after
        # task-started; at most 23s between sends or the task times out;
        # finish-task flushes buffered text. So a task starts on the turn's first
        # text and is finished early (not left to time out) before a pause: tool
        # calls, or IDLE_FINISH_SECONDS without text. The next text starts a new task.
        self._task_id = None
        self._task_open = False  # a task of this turn is accepting text
        self._task_ready = asyncio.Event()  # set on task-started
        self._task_done = asyncio.Event()  # set when the last task finished or failed
        self._task_done.set()
        self._early_finished_ids = set()  # finished early: the turn's playback continues
        self._last_text_time = 0.0

        # Model and voice configuration
        self.model = config.get("model", "cosyvoice-v2")
        self.voice = config.get("voice", "longxiaochun_v2")  # Default voice
        if config.get("private_voice"):
            self.voice = config.get("private_voice")

        # Audio parameter configuration
        self.format = config.get("format", "pcm")

        volume = config.get("volume", "50")
        self.volume = int(volume) if volume else 50

        rate = config.get("rate", "1.0")
        self.rate = float(rate) if rate else 1.0

        pitch = config.get("pitch", "1.0")
        self.pitch = float(pitch) if pitch else 1.0

        # Apply percentage adjustments (if present); otherwise use the public configuration
        self._apply_percentage_params(config)

        self.header = {
            "Authorization": f"Bearer {self.api_key}",
            # "user-agent": "your_platform_info", // optional
            # "X-DashScope-WorkSpace": workspace, // Optional, Alibaba Cloud Bailian business workspace ID
            "X-DashScope-DataInspection": "enable",
        }

    async def _ensure_connection(self):
        """Ensure the WebSocket connection is available, supporting reuse within 60 seconds"""
        try:
            current_time = time.time()
            if self.ws and current_time - self.last_active_time < 60:
                # The connection can be reused for continuous conversation only within one minute
                logger.bind(tag=TAG).debug(f"Using the existing connection...")
                return self.ws
            logger.bind(tag=TAG).debug("Establishing a new connection...")

            # Cancel the old monitor task before establishing a new connection
            await self._cancel_monitor_task()

            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=self.header,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                **self.ws_connect_options,
            )

            logger.bind(tag=TAG).debug("WebSocket connection established successfully")
            self.last_active_time = current_time
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to establish connection: {str(e)}")
            self.ws = None
            self.last_active_time = None
            raise

    def tts_text_priority_thread(self):
        """Streaming TTS text processing thread"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)

                if self.conn.client_abort:
                    try:
                        logger.bind(tag=TAG).info("Interruption received, terminating the TTS text processing thread")
                        if self._task_open and self._task_id:
                            self._task_open = False
                            asyncio.run_coroutine_threadsafe(
                                self.finish_session(self._task_id),
                                loop=self.conn.loop,
                            )
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to cancel TTS session: {str(e)}")
                        continue

                # Filter stale messages: check whether sentence_id matches
                if message.sentence_id != self.conn.sentence_id:
                    continue
                # Audio from here on belongs to this turn (handle_opus tags it)
                self.current_sentence_id = message.sentence_id

                logger.bind(tag=TAG).debug(
                    f"Received TTS task｜{message.sentence_type.name} ｜ {message.content_type.name} | Session ID: {message.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    # Reset streaming state; the Bailian task starts with the first text
                    self.reset_stream_state()
                    self.before_stop_play_files.clear()
                    self._task_open = False

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        try:
                            logger.bind(tag=TAG).debug(
                                f"Starting to send TTS text: {message.content_detail}"
                            )
                            future = asyncio.run_coroutine_threadsafe(
                                self._speak(message.content_detail),
                                loop=self.conn.loop,
                            )
                            future.result(timeout=self.tts_timeout)
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"Failed to send TTS text: {str(e)}")
                            continue

                elif ContentType.PAUSE == message.content_type:
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._finish_early("text pauses for tool calls"),
                            loop=self.conn.loop,
                        )
                        future.result(timeout=self.tts_timeout)
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to finish TTS task early: {str(e)}")

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Adding audio file to the playback queue: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Process the file's audio data first
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))

                if message.sentence_type == SentenceType.LAST:
                    try:
                        if self._task_open and self._task_id:
                            # task-finished ends the turn's playback
                            logger.bind(tag=TAG).debug("Ending the TTS session...")
                            self._task_open = False
                            future = asyncio.run_coroutine_threadsafe(
                                self.finish_session(self._task_id),
                                loop=self.conn.loop,
                            )
                            future.result()
                        else:
                            # No open task (no text, or finished early): end playback
                            # once any early-finished task has delivered its audio
                            future = asyncio.run_coroutine_threadsafe(
                                self._end_turn_without_task(),
                                loop=self.conn.loop,
                            )
                            future.result(timeout=self.tts_timeout + 1)
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to end TTS session: {str(e)}")
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to process TTS text: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    IDLE_FINISH_SECONDS = 20  # finish a waiting task well before Bailian's 23s limit

    async def _speak(self, text):
        """Send text, starting a task first if none is open."""
        if not (self._task_open and self.activate_session and self.ws):
            if self._task_open:
                logger.bind(tag=TAG).warning("TTS task ended unexpectedly; starting a new one")
            # One task at a time per connection: let a finishing task complete
            if not self._task_done.is_set():
                try:
                    await asyncio.wait_for(self._task_done.wait(), timeout=self.tts_timeout)
                except asyncio.TimeoutError:
                    logger.bind(tag=TAG).warning("Previous TTS task did not finish in time")
            self._task_id = uuid.uuid4().hex
            await self.start_session(self._task_id)
            # continue-task is allowed only after task-started
            await asyncio.wait_for(self._task_ready.wait(), timeout=self.tts_timeout)
            if not self.activate_session:
                raise RuntimeError("Bailian TTS task failed to start")
            self._task_open = True
            self._last_text_time = time.monotonic()
            asyncio.create_task(self._idle_watchdog(self._task_id))
        await self.text_to_speak(text, None)
        self._last_text_time = time.monotonic()

    async def _finish_early(self, reason):
        """finish-task before a pause: Bailian synthesizes the buffered text and the
        task ends cleanly instead of timing out. The turn's playback continues."""
        if not (self._task_open and self._task_id):
            return
        self._task_open = False
        self._early_finished_ids.add(self._task_id)
        logger.bind(tag=TAG).debug(f"Finishing TTS task early: {reason}")
        await self.finish_session(self._task_id)

    async def _idle_watchdog(self, task_id):
        while self._task_open and self._task_id == task_id:
            await asyncio.sleep(1)
            idle = time.monotonic() - self._last_text_time
            if self._task_open and self._task_id == task_id and idle > self.IDLE_FINISH_SECONDS:
                await self._finish_early(f"no text for {idle:.0f}s")
                return

    async def _end_turn_without_task(self):
        if not self._task_done.is_set():
            try:
                await asyncio.wait_for(self._task_done.wait(), timeout=self.tts_timeout)
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning("Early-finished TTS task did not finish in time")
        self._process_before_stop_play_files()

    async def text_to_speak(self, text, _):
        """Send text to the TTS service for synthesis"""
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning("WebSocket connection does not exist, stopping text sending")
                return

            # Filter Markdown
            filtered_text = MarkdownCleaner.clean_markdown(text)

            if filtered_text:
                # Use sliding-window matching to handle replacement words spanning chunks
                confirmed_texts, self._pending_prefix = self._match_stream_text(filtered_text)

                # Send each confirmed text fragment
                for txt in confirmed_texts:
                    if txt and self.ws:
                        continue_task_message = {
                            "header": {
                                "action": "continue-task",
                                "task_id": self._task_id,
                                "streaming": "duplex",
                            },
                            "payload": {"input": {"text": txt}},
                        }
                        await self.ws.send(json.dumps(continue_task_message))
                        self.last_active_time = time.time()
            return
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send TTS text: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
            raise

    async def start_session(self, session_id):
        """Start the TTS session"""
        logger.bind(tag=TAG).debug(f"Starting session ~~ {session_id}")
        try:
            # If the previous session is active, close the previous connection and create a new one
            if self.activate_session:
                await self.close()

            # Ensure the connection is available
            await self._ensure_connection()

            # Start the monitor task
            if self._monitor_task is None or self._monitor_task.done():
                logger.bind(tag=TAG).debug("Starting monitor task...")
                self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

            # Set the session state only now: replacing a stale connection
            # cancels the old monitor, whose cleanup resets it
            self.activate_session = True
            self._task_ready.clear()
            self._task_done.clear()

            # Send the run-task message to start the session
            run_task_message = {
                "header": {
                    "action": "run-task",
                    "task_id": session_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": self.model,
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": self.voice,
                        "format": self.format,
                        "sample_rate": self.conn.sample_rate,
                        "volume": self.volume,
                        "rate": self.rate,
                        "pitch": self.pitch,
                    },
                    "input": {}
                },
            }

            await self.ws.send(json.dumps(run_task_message))
            self.last_active_time = time.time()
            logger.bind(tag=TAG).debug("Session start request sent")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to start session: {str(e)}")
            await self.close()
            raise

    async def finish_session(self, session_id):
        """End the TTS session"""
        logger.bind(tag=TAG).debug(f"Closing session ~~ {session_id}")
        try:
            if self.ws and session_id:
                # Send the finish-task message
                finish_task_message = {
                    "header": {
                        "action": "finish-task",
                        "task_id": session_id,
                        "streaming": "duplex",
                    },
                    "payload": {
                        "input": {}
                    }
                }

                await self.ws.send(json.dumps(finish_task_message))
                self.last_active_time = time.time()

        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to close session: {str(e)}")
            await self.close()
            raise

    async def close(self):
        """Clean up resources"""
        await super().close()
        self.activate_session = False
        await self._cancel_monitor_task()

        # Close the WebSocket connection
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            self.last_active_time = None
    
    def interrupt(self):
        """The reply was interrupted: stop the task being synthesized now. The task
        protocol has no cancel (finish-task synthesizes everything buffered), so drop
        the connection; the next turn opens a new one."""
        if self._task_done.is_set() and not self._task_open:
            return
        if not (self.conn and self.conn.loop and self.ws):
            return
        logger.bind(tag=TAG).info("Interrupted: dropping the TTS task in progress")
        self._task_open = False
        self.activate_session = False
        ws = self.ws
        # The monitor sees the connection close, clears self.ws and marks the task done
        asyncio.run_coroutine_threadsafe(ws.close(), self.conn.loop)

    async def _cancel_monitor_task(self):
        """Cancel the monitor task"""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Error canceling monitor task: {e}")
        self._monitor_task = None

    async def _start_monitor_tts_response(self):
        """Monitor TTS responses - long-running"""
        try:
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()
                    self.last_active_time = time.time()

                    if isinstance(msg, str):  # JSON control message
                        try:
                            data = json.loads(msg)
                            header = data.get("header", {})
                            event = header.get("event")
                            task_id = header.get("task_id")

                            # Only handle responses for the currently active session
                            if task_id and self._task_id != task_id:
                                if event in ["task-finished", "task-failed"]:
                                    self._early_finished_ids.discard(task_id)
                                continue

                            if event == "task-started":
                                logger.bind(tag=TAG).debug("TTS task started successfully~")
                                self._task_ready.set()
                            elif event == "result-generated":
                                output = data.get("payload", {}).get("output", {})
                                if output.get("type") == "sentence-begin":
                                    original_text = output.get("original_text")
                                    self.tts_text = self._restore_original_text(original_text)
                                    logger.bind(tag=TAG).debug(f"Sentence speech generation started: {self.tts_text}")
                                    self.tts_audio_queue.put((SentenceType.FIRST, [], self.tts_text))
                                elif output.get("type") == "sentence-end":
                                    logger.bind(tag=TAG).info(f"Sentence speech generated successfully: {self.tts_text}")
                            elif event == "task-finished":
                                logger.bind(tag=TAG).debug("TTS task completed~")
                                self.activate_session = False
                                self._task_done.set()
                                if task_id in self._early_finished_ids:
                                    # Finished early before a pause: the turn goes on
                                    self._early_finished_ids.discard(task_id)
                                else:
                                    self._process_before_stop_play_files()
                            elif event == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "unknown error")
                                logger.bind(tag=TAG).error(
                                    f"TTS task failed: {error_code} - {error_message}"
                                )
                                # Wake a sender waiting for task-started; it sees the task is dead
                                self.activate_session = False
                                self._task_open = False
                                self._early_finished_ids.discard(task_id)
                                self._task_ready.set()
                                self._task_done.set()
                                break
                        except json.JSONDecodeError:
                            logger.bind(tag=TAG).warning("Received an invalid JSON message")
                    elif isinstance(msg, (bytes, bytearray)):
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            msg, False, callback=self.handle_opus
                        )
                except websockets.ConnectionClosed as e:
                    logger.bind(tag=TAG).warning(f"WebSocket connection closed: {e}")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Error while processing TTS response: {e}\n{traceback.format_exc()}"
                    )
                    break

            # Close the WebSocket when the connection is abnormal
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        # Clean up references when the monitor task exits
        finally:
            self.activate_session = False
            self._task_done.set()
            self._monitor_task = None

    def audio_to_opus_data_stream(
        self, audio_file_path, callback: Callable[[Any], Any] = None
    ):
        """Override the parent method: use a dedicated temporary encoder to process audio files,
        avoiding concurrency conflicts with the TTS streaming encoder.
        In dual-stream TTS, the monitor task receives TTS audio in the event loop thread and
        encodes it with self.opus_encoder, while tts_text_priority_thread also uses
        self.opus_encoder when processing music files. The shared encoder.buffer is not
        thread-safe, and concurrent access causes SILK resampler assertion failures.
        """
        from core.utils.util import audio_to_data_stream

        return audio_to_data_stream(
            audio_file_path,
            is_opus=True,
            callback=callback,
            sample_rate=self.conn.sample_rate,
            opus_encoder=None,
        )

    def to_tts(self, text: str) -> list:
        """Generate audio data in non-streaming mode, used for audio generation and testing"""
        try:
            # Create an event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Generate a session ID
            session_id = uuid.uuid4().hex
            # Store audio data
            audio_data = []
            # Own encoder: this runs in a worker thread while self.opus_encoder may be
            # encoding a reply, and the shared buffer would mix the two
            encoder = OpusEncoderUtils(
                sample_rate=self.conn.sample_rate, channels=1, frame_size_ms=60
            )

            async def _generate_audio():
                ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=self.header,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                    **self.ws_connect_options,
                )

                try:
                    # Send the run-task message to start the session
                    run_task_message = {
                        "header": {
                            "action": "run-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "task_group": "audio",
                            "task": "tts",
                            "function": "SpeechSynthesizer",
                            "model": self.model,
                            "parameters": {
                                "text_type": "PlainText",
                                "voice": self.voice,
                                "format": self.format,
                                "sample_rate": self.conn.sample_rate,
                                "volume": self.volume,
                                "rate": self.rate,
                                "pitch": self.pitch,
                            },
                            "input": {}
                        },
                    }
                    await ws.send(json.dumps(run_task_message))

                    # Wait for the task to start
                    task_started = False
                    while not task_started:
                        msg = await ws.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-started":
                                task_started = True
                                logger.bind(tag=TAG).debug("TTS task started")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "unknown error")
                                raise Exception(
                                    f"Failed to start task: {error_code} - {error_message}"
                                )

                    # Send text
                    filtered_text = MarkdownCleaner.clean_markdown(text)
                    if self._correct_words_pattern:
                        filtered_text = self._correct_words_pattern.sub(lambda m: self.correct_words[m.group(0)], filtered_text)
                    # Send the continue-task message
                    continue_task_message = {
                        "header": {
                            "action": "continue-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {"input": {"text": filtered_text}},
                    }
                    await ws.send(json.dumps(continue_task_message))

                    # Send the finish-task message
                    finish_task_message = {
                        "header": {
                            "action": "finish-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "input": {}
                        }
                    }
                    await ws.send(json.dumps(finish_task_message))

                    # Receive audio data
                    task_finished = False
                    while not task_finished:
                        msg = await ws.recv()
                        if isinstance(msg, (bytes, bytearray)):
                            encoder.encode_pcm_to_opus_stream(
                                msg,
                                end_of_stream=False,
                                callback=audio_data.append
                            )
                        elif isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-finished":
                                task_finished = True
                                # Flush the last partial frame, or the clip loses its end
                                encoder.encode_pcm_to_opus_stream(
                                    b"", end_of_stream=True, callback=audio_data.append
                                )
                                logger.bind(tag=TAG).debug("TTS task completed")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "unknown error")
                                raise Exception(
                                    f"Synthesis failed: {error_code} - {error_message}"
                                )

                finally:
                    # Clean up resources
                    try:
                        await ws.close()
                    except:
                        pass

            # Run the async task
            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data

        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to generate audio data: {str(e)}")
            return []
