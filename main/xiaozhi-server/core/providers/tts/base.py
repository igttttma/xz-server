import os
import re
import math
import uuid
import queue
import asyncio
import threading
import traceback

from core.utils import p3
from datetime import datetime
from core.utils import textUtils
from typing import Callable, Any, Optional
from abc import ABC, abstractmethod
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.tts import MarkdownCleaner, convert_percentage_to_range
from core.utils.output_counter import add_device_output
from core.handle.reportHandle import enqueue_tts_report
from core.handle.sendAudioHandle import sendAudioMessage
from core.utils.util import audio_bytes_to_data_stream, audio_to_data_stream
from core.providers.tts.dto.dto import (
    TTSMessageDTO,
    SentenceType,
    ContentType,
    InterfaceType,
)

TAG = __name__
logger = setup_logging()


class TTSProviderBase(ABC):
    def __init__(self, config, delete_audio_file):
        self.interface_type = InterfaceType.NON_STREAM
        self.conn = None
        self.delete_audio_file = delete_audio_file
        self.audio_file_type = "wav"
        self.output_file = config.get("output_dir", "tmp/")
        self.tts_timeout = float(config.get("tts_timeout", 15))
        if not math.isfinite(self.tts_timeout) or self.tts_timeout <= 0:
            raise ValueError("tts_timeout must be a positive finite number")
        self.tts_text_queue = queue.Queue()
        self.tts_audio_queue = queue.Queue()
        self.tts_audio_first_sentence = True
        self.before_stop_play_files = []
        self.report_on_last = False
        # Mapping from sentence_id to text, used by streaming TTS to get the correct subtitle text
        self._sentence_text_map = {}
        # Load replacement words for one-pass regex replacement
        raw_words = config.get("correct_words", [])
        self.correct_words = {}
        for item in raw_words:
            parts = item.split("|", 1)
            if len(parts) == 2:
                self.correct_words[parts[0]] = parts[1]
        # Build the regex, preferring the longest match (sorted, escaped and joined)
        if self.correct_words:
            # Sort keys by length descending so longer words match first and short words do not interfere
            sorted_keys = sorted(self.correct_words.keys(), key=len, reverse=True)
            pattern_str = "|".join(re.escape(k) for k in sorted_keys)
            self._correct_words_pattern = re.compile(pattern_str)
            # Build the reverse replacement regex to restore the replaced text returned by the TTS service to the original text (for subtitles)
            reverse_map = {v: k for k, v in self.correct_words.items()}
            sorted_reverse_keys = sorted(reverse_map.keys(), key=len, reverse=True)
            reverse_pattern_str = "|".join(re.escape(k) for k in sorted_reverse_keys)
            self._reverse_words_pattern = re.compile(reverse_pattern_str)
            self._reverse_words_map = reverse_map
            # Streaming sliding window: dictionary of replacement words grouped by first character for fast lookup
            self._words_by_first_char = {}
            for key in sorted_keys:  # Use the keys already sorted by length descending to ensure longer words match first
                first_char = key[0] if key else ""
                if first_char not in self._words_by_first_char:
                    self._words_by_first_char[first_char] = []
                self._words_by_first_char[first_char].append(key)
        else:
            self._correct_words_pattern = None
            self._reverse_words_pattern = None
            self._reverse_words_map = None

        # Streaming sliding window: buffered text awaiting matching
        self._pending_prefix = ""
        self.tts_text_buff = []
        self.punctuations = (
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
        )
        self.first_sentence_punctuations = (
            "，",
            "~",
            "、",
            ",",
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
        )
        self.tts_stop_request = False
        self.processed_chars = 0
        self.is_first_sentence = True

    def generate_filename(self, extension=".wav"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    def handle_opus(self, opus_data: bytes):
        logger.bind(tag=TAG).debug(f"Pushing data to the queue, frame count ~~ {len(opus_data)}")
        self.tts_audio_queue.put((SentenceType.MIDDLE, opus_data, None, getattr(self, 'current_sentence_id', None)))

    def handle_audio_file(self, file_audio: bytes, text):
        self.before_stop_play_files.append((file_audio, text))

    def to_tts_stream(self, text, opus_handler: Callable[[bytes], None] = None) -> None:
        # Keep the original text for display/reporting
        original_text = text
        text = MarkdownCleaner.clean_markdown(text)
        # Replace in one regex pass to avoid repeated traversal and partial-match issues
        if self._correct_words_pattern:
            text = self._correct_words_pattern.sub(lambda m: self.correct_words[m.group(0)], text)
        max_repeat_time = 5
        if self.delete_audio_file:
            # When the file is to be deleted, convert directly to audio data
            while max_repeat_time > 0:
                try:
                    audio_bytes = asyncio.run(self.text_to_speak(text, None))
                    if audio_bytes:
                        # Use the original text for display/reporting
                        self.tts_audio_queue.put((SentenceType.FIRST, None, original_text, getattr(self, 'current_sentence_id', None)))
                        audio_bytes_to_data_stream(
                            audio_bytes,
                            file_type=self.audio_file_type,
                            is_opus=True,
                            callback=opus_handler,
                            sample_rate=self.conn.sample_rate,
                            opus_encoder=self.opus_encoder,
                        )
                        break
                    else:
                        max_repeat_time -= 1
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"Speech generation failed attempt {5 - max_repeat_time + 1}: {original_text}, error: {e}"
                    )
                    max_repeat_time -= 1
            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"Speech generated successfully: {original_text}, after {5 - max_repeat_time} retries"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"Speech generation failed: {original_text}, please check whether the network or service is working normally"
                )
            return None
        else:
            tmp_file = self.generate_filename()
            try:
                while not os.path.exists(tmp_file) and max_repeat_time > 0:
                    try:
                        asyncio.run(self.text_to_speak(text, tmp_file))
                    except Exception as e:
                        logger.bind(tag=TAG).warning(
                            f"Speech generation failed attempt {5 - max_repeat_time + 1}: {original_text}, error: {e}"
                        )
                        # Execution did not succeed; delete the file
                        if os.path.exists(tmp_file):
                            os.remove(tmp_file)
                        max_repeat_time -= 1

                if max_repeat_time > 0:
                    logger.bind(tag=TAG).info(
                        f"Speech generated successfully: {original_text}:{tmp_file}, after {5 - max_repeat_time} retries"
                    )
                else:
                    logger.bind(tag=TAG).error(
                        f"Speech generation failed: {original_text}, please check whether the network or service is working normally"
                    )
                self.tts_audio_queue.put((SentenceType.FIRST, None, original_text, getattr(self, 'current_sentence_id', None)))
                self._process_audio_file_stream(tmp_file, callback=opus_handler)
            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
                return None
    
    def to_tts(self, text):
        # Keep the original text for logging/display
        original_text = text
        text = MarkdownCleaner.clean_markdown(text)
        if self._correct_words_pattern:
            text = self._correct_words_pattern.sub(lambda m: self.correct_words[m.group(0)], text)
        max_repeat_time = 5
        if self.delete_audio_file:
            # When the file is to be deleted, convert directly to audio data
            while max_repeat_time > 0:
                try:
                    audio_bytes = asyncio.run(self.text_to_speak(text, None))
                    if audio_bytes:
                        audio_datas = []
                        audio_bytes_to_data_stream(
                            audio_bytes,
                            file_type=self.audio_file_type,
                            is_opus=True,
                            callback=lambda data: audio_datas.append(data),
                            sample_rate=self.conn.sample_rate,
                        )
                        return audio_datas
                    else:
                        max_repeat_time -= 1
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"Speech generation failed attempt {5 - max_repeat_time + 1}: {original_text}, error: {e}"
                    )
                    max_repeat_time -= 1
            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"Speech generated successfully: {original_text}, after {5 - max_repeat_time} retries"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"Speech generation failed: {original_text}, please check whether the network or service is working normally"
                )
            return None
        else:
            tmp_file = self.generate_filename()
            try:
                while not os.path.exists(tmp_file) and max_repeat_time > 0:
                    try:
                        asyncio.run(self.text_to_speak(text, tmp_file))
                    except Exception as e:
                        logger.bind(tag=TAG).warning(
                            f"Speech generation failed attempt {5 - max_repeat_time + 1}: {original_text}, error: {e}"
                        )
                        # Execution did not succeed; delete the file
                        if os.path.exists(tmp_file):
                            os.remove(tmp_file)
                        max_repeat_time -= 1

                if max_repeat_time > 0:
                    logger.bind(tag=TAG).info(
                        f"Speech generated successfully: {original_text}:{tmp_file}, after {5 - max_repeat_time} retries"
                    )
                else:
                    logger.bind(tag=TAG).error(
                        f"Speech generation failed: {original_text}, please check whether the network or service is working normally"
                    )

                return tmp_file
            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
                return None

    @abstractmethod
    async def text_to_speak(self, text, output_file):
        pass

    def audio_to_pcm_data_stream(
        self, audio_file_path, callback: Callable[[Any], Any] = None
    ):
        """Convert an audio file to PCM encoding"""
        return audio_to_data_stream(audio_file_path, is_opus=False, callback=callback, sample_rate=self.conn.sample_rate, opus_encoder=None)

    def audio_to_opus_data_stream(
        self, audio_file_path, callback: Callable[[Any], Any] = None
    ):
        """Convert an audio file to Opus encoding"""
        return audio_to_data_stream(audio_file_path, is_opus=True, callback=callback, sample_rate=self.conn.sample_rate, opus_encoder=self.opus_encoder)

    def tts_one_sentence(
        self,
        conn,
        content_type,
        content_detail=None,
        content_file=None,
        sentence_id=None,
    ):
        """Send a single sentence"""
        if not sentence_id:
            if conn.sentence_id:
                sentence_id = conn.sentence_id
            else:
                sentence_id = str(uuid.uuid4().hex)
                conn.sentence_id = sentence_id
        # Split the single-sentence text into segments
        segments = re.split(r"([。！？!?；;\n])", content_detail)
        for seg in segments:
            self.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=content_type,
                    content_detail=seg,
                    content_file=content_file,
                )
            )

    async def open_audio_channels(self, conn):
        self.conn = conn

        # Create the encoder from conn.sample_rate unless the subclass already created one (the IndexTTS API returns 24 kHz audio that needs resampling)
        if not hasattr(self, 'opus_encoder') or self.opus_encoder is None:
            self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
                sample_rate=conn.sample_rate, channels=1, frame_size_ms=60
            )

        # TTS consumer thread
        self.tts_priority_thread = threading.Thread(
            target=self.tts_text_priority_thread, daemon=True
        )
        self.tts_priority_thread.start()

        # Audio playback consumer thread
        self.audio_play_priority_thread = threading.Thread(
            target=self._audio_play_priority_thread, daemon=True
        )
        self.audio_play_priority_thread.start()

    def store_tts_text(self, sentence_id, text):
        """Store the text for the given sentence_id so streaming TTS can get the correct subtitle text

        Args:
            sentence_id: session ID
            text: text to store
        """
        if sentence_id and text:
            self._sentence_text_map[sentence_id] = text
            # Keep only the latest 5 entries to prevent memory leaks
            if len(self._sentence_text_map) > 5:
                oldest = next(iter(self._sentence_text_map))
                del self._sentence_text_map[oldest]

    def get_tts_text(self, sentence_id):
        """Get the text for the given sentence_id

        Args:
            sentence_id: session ID

        Returns:
            str: the corresponding text, or None if it does not exist
        """
        return self._sentence_text_map.get(sentence_id)

    def clear_tts_text(self, sentence_id):
        """Clear the text for the given sentence_id

        Args:
            sentence_id: session ID
        """
        if sentence_id in self._sentence_text_map:
            del self._sentence_text_map[sentence_id]

    def _restore_original_text(self, text):
        if not self._reverse_words_pattern or not text:
            return text
        return self._reverse_words_pattern.sub(
            lambda m: self._reverse_words_map[m.group(0)], text
        )

    # The default handling here is non-streaming
    # Override it in a subclass for streaming handling
    def tts_text_priority_thread(self):
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("Interruption received, terminating the TTS text processing thread")
                    continue
                # Filter stale messages: check whether sentence_id matches
                if message.sentence_id != self.conn.sentence_id:
                    continue
                if message.sentence_type == SentenceType.FIRST:
                    self.current_sentence_id = message.sentence_id
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.is_first_sentence = True
                    self.tts_audio_first_sentence = True
                elif ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        self.to_tts_stream(segment_text, opus_handler=self.handle_opus)
                elif ContentType.FILE == message.content_type:
                    self._process_remaining_text_stream(opus_handler=self.handle_opus)
                    tts_file = message.content_file
                    if tts_file and os.path.exists(tts_file):
                        self._process_audio_file_stream(
                            tts_file, callback=self.handle_opus
                        )
                if message.sentence_type == SentenceType.LAST:
                    self._process_remaining_text_stream(opus_handler=self.handle_opus)
                    self.tts_audio_queue.put(
                        (message.sentence_type, [], message.content_detail, message.sentence_id)
                    )

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to process TTS text: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    def _audio_play_priority_thread(self):
        # Text and audio lists that need to be reported
        enqueue_text = None
        enqueue_audio = []
        while not self.conn.stop_event.is_set():
            text = None
            try:
                try:
                    item = self.tts_audio_queue.get(timeout=0.1)
                    if len(item) == 4:
                        sentence_type, audio_datas, text, sentence_id = item
                    else:
                        sentence_type, audio_datas, text = item
                        sentence_id = None
                except queue.Empty:
                    if self.conn.stop_event.is_set():
                        break
                    continue

                if self.conn.client_abort:
                    logger.bind(tag=TAG).debug("Interruption signal received, skipping the current audio data")
                    enqueue_text, enqueue_audio = None, []
                    continue

                # Audio of an earlier turn (an interrupted reply still arriving)
                if sentence_id and sentence_id != self.conn.sentence_id:
                    continue

                # Report when the next text starts or the session ends
                if sentence_type is not SentenceType.MIDDLE:
                    if self.report_on_last:
                        # Accumulation mode: for TTS with a single continuous audio stream (e.g. seed-tts-2.0)
                        # On FIRST only record the text; audio keeps accumulating and is reported only on LAST
                        if text:
                            enqueue_text = text
                        if sentence_type == SentenceType.LAST:
                            enqueue_tts_report(self.conn, enqueue_text, enqueue_audio)
                            enqueue_audio = []
                            enqueue_text = None
                    else:
                        # Non-accumulation mode: report each sentence separately
                        if enqueue_text is not None:
                            enqueue_tts_report(self.conn, enqueue_text, enqueue_audio)
                        enqueue_audio = []
                        enqueue_text = text

                # Collect audio data for reporting
                if isinstance(audio_datas, bytes):
                    enqueue_audio.append(audio_datas)

                # Send audio
                future = asyncio.run_coroutine_threadsafe(
                    sendAudioMessage(self.conn, sentence_type, audio_datas, text, sentence_id),
                    self.conn.loop,
                )
                future.result()

                # Record output and reports
                if self.conn.max_output_size > 0 and text:
                    add_device_output(self.conn.headers.get("device-id"), len(text))

            except Exception as e:
                logger.bind(tag=TAG).error(f"audio_play_priority_thread: {text} {e}")

    async def start_session(self, session_id):
        pass

    async def finish_session(self, session_id):
        pass

    async def close(self):
        """Resource cleanup method"""
        self._sentence_text_map.clear()
        if hasattr(self, "ws") and self.ws:
            await self.ws.close()

    # Right quotes/brackets and their corresponding left-side symbols
    _QUOTE_PAIRS = (
        ("「", "」"),
        ("『", "』"),
        ("“", "”"),
        ('"', '"'),
        ("（", "）"),
        ("《", "》"),
        ("«", "»"),
        ("„", "“"),
        ("【", "】"),
        ("〈", "〉"),
        ("［", "］"),
        ("[", "]"),
    )
    # Note: “ (U+201C) has dual semantics: in Chinese it is an opening quote (paired with ”),
    # while in German „…“ it is a closing quote; when the two conflict, counting cannot handle both,
    # so German sentence splitting can only be handled conservatively by "defer when unbalanced" (with flush as the final fallback).
    _CLOSERS = '」』”》）"»“】〉］]'
    _QUOTE_CHARS = "".join(ch for pair in _QUOTE_PAIRS for ch in pair)

    @classmethod
    def _quote_safe_cut(cls, text: str, pos: int, punctuations) -> int:
        """Avoid splitting inside quotes (e.g. 「わぁ！」って / “Good!” he said).

        Any closing quote and sentence-final punctuation immediately following the candidate
        position are carried along; if the candidate is inside an unclosed quote, or the
        sentence continues after the closing quote, defer to the next punctuation mark;
        if none is safe, return -1 and wait for more text.
        """
        if not any(ch in cls._QUOTE_CHARS for ch in text):
            # No quotes/brackets in the whole text: there is no unclosed quote and no closing quote to carry, so the candidate position is always safe
            return pos
        candidates = [pos] + [
            i for i, ch in enumerate(text) if i > pos and ch in punctuations
        ]
        for candidate in candidates:
            end = candidate + 1
            carried_closer = False
            while end < len(text) and (
                text[end] in cls._CLOSERS or text[end] in punctuations
            ):
                if text[end] in cls._CLOSERS:
                    carried_closer = True
                end += 1
            segment = text[:end]
            # Paired quotes (「」 etc.) are detected by count difference; same-character quotes (") by parity
            balanced = True
            for opener, closer in cls._QUOTE_PAIRS:
                n_open = segment.count(opener)
                if opener == closer:
                    if n_open % 2:
                        balanced = False
                        break
                elif n_open > segment.count(closer):
                    balanced = False
                    break
            if not balanced:
                continue
            if carried_closer and (end == len(text) or not text[end].isspace()):
                # The sentence continues after the closing quote (「…」って, “…” he said), or no following text is visible yet
                continue
            return end - 1
        return -1

    def _get_segment_text(self) -> Optional[str]:
        # Merge all current text and process the unsplit part
        full_text = "".join(self.tts_text_buff)
        current_text = full_text[self.processed_chars :]  # Start from the unprocessed position
        last_punct_pos = -1

        # Choose a different punctuation set depending on whether this is the first sentence
        punctuations_to_use = (
            self.first_sentence_punctuations
            if self.is_first_sentence
            else self.punctuations
        )

        # Take the earliest of the last occurrence of each punctuation as the split point (equivalent to repeated rfind and taking the minimum)
        last_seen = {}
        for i, ch in enumerate(current_text):
            if ch in punctuations_to_use:
                last_seen[ch] = i
        last_punct_pos = min(last_seen.values(), default=-1)

        cut_pos = -1
        if last_punct_pos != -1:
            cut_pos = self._quote_safe_cut(
                current_text, last_punct_pos, punctuations_to_use
            )
        if cut_pos != -1:
            segment_text_raw = current_text[: cut_pos + 1]
            segment_text = textUtils.get_string_no_punctuation_or_emoji(
                segment_text_raw
            )
            self.processed_chars += len(segment_text_raw)  # Update the processed character position

            # If this is the first sentence, set the flag to False after finding the first comma
            if self.is_first_sentence:
                self.is_first_sentence = False

            return segment_text
        elif self.tts_stop_request and current_text:
            segment_text = current_text
            self.is_first_sentence = True  # Reset the flag
            return segment_text
        else:
            return None

    def _process_audio_file_stream(
        self, tts_file, callback: Callable[[Any], Any]
    ) -> None:
        """Process an audio file and convert it to the specified format

        Args:
            tts_file: audio file path
            callback: file processing callback
        """
        if tts_file.endswith(".p3"):
            p3.decode_opus_from_file_stream(tts_file, callback=callback)
        elif self.conn.audio_format == "pcm":
            self.audio_to_pcm_data_stream(tts_file, callback=callback)
        else:
            self.audio_to_opus_data_stream(tts_file, callback=callback)

        if (
            self.delete_audio_file
            and tts_file is not None
            and os.path.exists(tts_file)
            and tts_file.startswith(self.output_file)
        ):
            os.remove(tts_file)

    def _process_before_stop_play_files(self):
        for audio_datas, text in self.before_stop_play_files:
            self.tts_audio_queue.put((SentenceType.MIDDLE, audio_datas, text, getattr(self, 'current_sentence_id', None)))
        self.before_stop_play_files.clear()
        self.tts_audio_queue.put((SentenceType.LAST, [], None, getattr(self, 'current_sentence_id', None)))

    def _process_remaining_text_stream(
        self, opus_handler: Callable[[bytes], None] = None
    ):
        """Process the remaining text and generate speech

        Returns:
            bool: whether the text was processed successfully
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                self.to_tts_stream(segment_text, opus_handler=opus_handler)
                self.processed_chars += len(full_text)
                return True
        return False

    def _apply_percentage_params(self, config):
        """Apply percentage parameters in bulk according to TTS_PARAM_CONFIG defined by the subclass"""
        for config_key, attr_name, min_val, max_val, base_val, transform in self.TTS_PARAM_CONFIG:
            if config_key in config:
                val = convert_percentage_to_range(config[config_key], min_val, max_val, base_val)
                setattr(self, attr_name, transform(val) if transform else val)

    def _match_stream_text(self, text):
        """Streaming text sliding-window matching, used for replacement words spanning chunks

        Args:
            text: input text fragment

        Returns:
            tuple: (list of confirmed texts, remaining prefix awaiting matching)
        """
        if not self.correct_words or not text:
            return [text] if text else [], ""

        result = []
        pending = self._pending_prefix
        i = 0

        while i < len(text):
            char = text[i]

            # Try whether pending + current character matches a replacement word
            test_text = pending + char

            matched = False
            # Iterate over possibly matching replacement words
            candidates = self._words_by_first_char.get(pending[0], []) if pending else self._words_by_first_char.get(char, [])
            for key in candidates:
                if test_text == key:
                    # Complete match: send the replacement
                    result.append(self.correct_words[key])
                    pending = ""
                    matched = True
                    break
                elif key.startswith(test_text):
                    # Prefix of a replacement word: keep waiting
                    pending = test_text
                    matched = True
                    break

            if matched:
                i += 1
                continue

            # No longer word matched; the pending content can be sent
            if pending:
                result.append(pending)
                pending = ""

            # Check whether the current character starts a replacement word
            if char in self._words_by_first_char:
                pending = char
            else:
                result.append(char)

            i += 1

        return result, pending

    def reset_stream_state(self):
        """Reset streaming state to clear leftover state when a session starts"""
        self._pending_prefix = ""
