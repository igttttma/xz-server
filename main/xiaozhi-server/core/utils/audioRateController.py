import time
import asyncio
from collections import deque
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class AudioRateController:
    """
    Audio rate controller - precisely controls audio sending using a 60ms frame duration,
    solving cumulative timing drift under high concurrency.
    """

    def __init__(self, frame_duration=60, send_delay=0):
        """
        Args:
            frame_duration: duration of a single audio frame (milliseconds), 60ms by default
            send_delay: custom send interval (milliseconds).
                        0 = send at the frame_duration pace;
                        >0 = send at the send_delay pace (no queueing delay on the main thread, no pre-buffer)
        """
        # Flow control interval (milliseconds): use the configured value when send_delay > 0, otherwise frame_duration
        self.interval_ms = send_delay if send_delay > 0 else frame_duration
        self.queue = deque()
        self.play_position = 0  # virtual playback position (milliseconds)
        self.start_timestamp = None  # start timestamp (read-only, never modified)
        self.pending_send_task = None
        self.logger = logger
        self.queue_empty_event = asyncio.Event()  # queue-empty event
        self.queue_empty_event.set()  # start in the empty state
        self.queue_has_data_event = asyncio.Event()  # queue-has-data event
        self._last_queue_empty_time = 0  # time the queue last became empty (seconds)

    def reset(self):
        """Reset the controller state"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            # After cancelling, the task is cleaned up on the next event loop iteration; no need to block and wait

        self.queue.clear()
        self.play_position = 0
        self.start_timestamp = None  # set by the first audio packet
        self._last_queue_empty_time = 0  # reset the time
        # Update the related events
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()

    def add_audio(self, opus_packet):
        """Add an audio packet to the queue"""
        # If the queue was empty, adjust the timestamp to keep playback time continuous,
        # so audio added while waiting for a tool call is not played early.
        # If the gap is very short (<1 frame), this is normal streaming and no reset is needed.
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            # Only a gap longer than one frame counts as a real "pause and resume"
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed from empty, timestamp reset, current playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("audio", opus_packet))
        # Update the related events
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def add_message(self, message_callback):
        """
        Add a message to the queue (sent immediately, does not consume playback time).

        Args:
            message_callback: message sending callback async def()
        """
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed from empty, timestamp reset, current playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("message", message_callback))
        # Update the related events
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def _get_elapsed_ms(self):
        """Get the elapsed time (milliseconds)"""
        if self.start_timestamp is None:
            return 0
        return (time.monotonic() - self.start_timestamp) * 1000

    async def check_queue(self, send_audio_callback):
        """
        Check the queue and send audio/messages on schedule.

        Args:
            send_audio_callback: audio sending callback async def(opus_packet)
        """
        while self.queue:
            item = self.queue[0]
            item_type = item[0]

            if item_type == "message":
                # Message type: send immediately, does not consume playback time
                _, message_callback = item
                self.queue.popleft()
                try:
                    await message_callback()
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send message: {e}")
                    raise

            elif item_type == "audio":
                if self.start_timestamp is None:
                    self.start_timestamp = time.monotonic()

                _, opus_packet = item

                # Loop until the scheduled time is reached
                while True:
                    # Compute the time difference
                    elapsed_ms = self._get_elapsed_ms()
                    output_ms = self.play_position

                    if elapsed_ms < output_ms:
                        # Not yet time to send; compute the wait duration
                        wait_ms = output_ms - elapsed_ms

                        # Check again after waiting (can be interrupted)
                        try:
                            await asyncio.sleep(wait_ms / 1000)
                        except asyncio.CancelledError:
                            self.logger.bind(tag=TAG).debug("Audio sending task cancelled")
                            raise
                        # Recheck the time after waiting (loop back to while True)
                    else:
                        # Time is up; exit the wait loop
                        break

                # Time is up; remove from the queue and send
                self.queue.popleft()
                self.play_position += self.interval_ms
                try:
                    await send_audio_callback(opus_packet)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send audio: {e}")
                    raise

        # Clear the events once the queue is drained
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()
        self._last_queue_empty_time = time.monotonic()  # record when the queue became empty

    def start_sending(self, send_audio_callback):
        """
        Start the async sending task.

        Args:
            send_audio_callback: audio sending callback

        Returns:
            asyncio.Task: the sending task
        """

        async def _send_loop():
            try:
                while True:
                    # Wait on the queue-has-data event instead of busy polling and wasting CPU
                    await self.queue_has_data_event.wait()

                    await self.check_queue(send_audio_callback)
            except asyncio.CancelledError:
                self.logger.bind(tag=TAG).debug("Audio sending loop stopped")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Audio sending loop error: {e}")

        self.pending_send_task = asyncio.create_task(_send_loop())
        return self.pending_send_task

    def stop_sending(self):
        """Stop the sending task"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            self.logger.bind(tag=TAG).debug("Audio sending task cancelled")
