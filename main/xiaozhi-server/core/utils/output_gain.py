"""
Volume boost for the audio sent to the client (portal "TTS volume boost").

Applied in sendAudio, so every reply path (streaming TTS, cached greetings,
notification sounds) gets the same boost. Opus packets are decoded, amplified
and re-encoded; PCM is amplified directly. A peak limiter lowers the gain where
the boosted signal would clip instead of hard-clipping it.
"""

import logging

import numpy as np
import opuslib_next
from opuslib_next import constants

# Peak ceiling after the boost (about -0.5 dBFS)
LIMIT = 32767 * 0.94
# How fast the gain recovers after the limiter pulled it down (dB per second)
RELEASE_DB_PER_S = 20
MAX_FRAME_MS = 120


class OutputGain:
    def __init__(self, gain_db: float, sample_rate: int, audio_format: str):
        self.gain_db = gain_db
        self.sample_rate = sample_rate
        self.audio_format = audio_format
        self.target = 10 ** (gain_db / 20)
        self.current = self.target
        self.decoder = None
        self.encoder = None
        if audio_format != "pcm":
            self.decoder = opuslib_next.Decoder(sample_rate, 1)
            # Same settings as OpusEncoderUtils, which encodes the TTS audio
            self.encoder = opuslib_next.Encoder(sample_rate, 1, constants.APPLICATION_AUDIO)
            self.encoder.bitrate = 24000
            self.encoder.complexity = 10
            self.encoder.signal = constants.SIGNAL_VOICE

    def matches(self, gain_db: float, sample_rate: int, audio_format: str) -> bool:
        return (self.gain_db, self.sample_rate, self.audio_format) == (gain_db, sample_rate, audio_format)

    def process(self, packet: bytes) -> bytes:
        try:
            if self.decoder is None:
                return self._amplify(packet)
            pcm = self.decoder.decode(bytes(packet), self.sample_rate * MAX_FRAME_MS // 1000)
            samples = len(pcm) // 2
            return self.encoder.encode(self._amplify(pcm), samples)
        except Exception as e:
            # Better unboosted than silent
            logging.error(f"Output gain failed, sending the packet unchanged: {e}")
            return packet

    def _amplify(self, pcm: bytes) -> bytes:
        frame = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        if frame.size == 0:
            return pcm
        peak = float(np.max(np.abs(frame)))
        allowed = LIMIT / peak if peak > 0 else self.target
        release = 10 ** (RELEASE_DB_PER_S * frame.size / self.sample_rate / 20)
        end = min(self.target, allowed, self.current * release)
        if end < self.current:
            # Limiting: duck the whole frame at once so its peak cannot clip
            gains = np.full(frame.size, end, dtype=np.float32)
        else:
            # Recovering: ramp smoothly to avoid zipper noise
            gains = np.linspace(self.current, end, frame.size, dtype=np.float32)
        self.current = end
        return np.clip(frame * gains, -32768, 32767).astype(np.int16).tobytes()


def output_gain_for(conn):
    """The connection's OutputGain, or None when no boost is configured."""
    try:
        gain_db = float(conn.config.get("tts_gain_db", 0) or 0)
    except (TypeError, ValueError):
        gain_db = 0
    if gain_db <= 0:
        return None
    gain = getattr(conn, "_output_gain", None)
    if gain is None or not gain.matches(gain_db, conn.sample_rate, conn.audio_format):
        gain = OutputGain(gain_db, conn.sample_rate, conn.audio_format)
        conn._output_gain = gain
    return gain
