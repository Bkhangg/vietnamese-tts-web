"""
Silence generation and audio concatenation engine.
Processes audio in chunks to avoid high memory usage.
"""

import os
import tempfile
from pathlib import Path
from typing import Iterator, Optional, Generator

from pydub import AudioSegment, generators


class SilenceEngine:
    """
    Generates silence segments and stitches audio chunks together.
    Can work in streaming mode for long texts.
    """

    SAMPLE_RATE = 22050
    CHANNELS = 1
    SAMPLE_WIDTH = 2

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self._temp_dir = tempfile.mkdtemp(prefix="tts_silence_")
        self._chunk_count = 0

    def make_silence(self, duration_ms: int) -> AudioSegment:
        """Create a silent AudioSegment of the given duration."""
        if duration_ms <= 0:
            duration_ms = 1
        return AudioSegment.silent(
            duration=duration_ms,
            frame_rate=self.sample_rate,
        )

    def save_chunk(self, audio: AudioSegment) -> str:
        """Save an audio chunk to a temporary file and return its path."""
        path = os.path.join(self._temp_dir, f"chunk_{self._chunk_count:06d}.wav")
        self._chunk_count += 1
        audio.export(path, format="wav", parameters=["-ac", "1"])
        return path

    def stitch_to_file(
        self,
        segments: Iterator[AudioSegment],
        output_path: str,
        batch_size: int = 50,
    ) -> str:
        """
        Concatenate many AudioSegments in batches to avoid OOM.
        Writes intermediate WAV files, then merges them.
        """
        import shutil
        output_path = str(output_path)
        batch_paths = []
        batch = AudioSegment.empty()

        for i, seg in enumerate(segments):
            batch += seg
            if (i + 1) % batch_size == 0:
                batch_paths.append(self.save_chunk(batch))
                batch = AudioSegment.empty()

        if len(batch) > 0:
            batch_paths.append(self.save_chunk(batch))

        if not batch_paths:
            self._cleanup()
            return ""

        combined = AudioSegment.empty()
        for bp in batch_paths:
            combined += AudioSegment.from_file(bp, format="wav")

        if output_path.endswith(".mp3"):
            combined.export(output_path, format="mp3", bitrate="48k")
        else:
            combined.export(output_path, format="wav")

        self._cleanup()
        return output_path

    def stitch_stream(
        self,
        segments: Generator[AudioSegment, None, None],
        output_path: str,
        flush_interval: int = 100,
    ) -> str:
        """
        Streaming variant: writes audio sequentially, flushing every N chunks.
        Best for very long texts (10k+ sentences).
        """
        output_path = str(output_path)
        temp_wav = os.path.join(self._temp_dir, "stream_output.wav")

        combined = AudioSegment.silent(duration=0, frame_rate=self.sample_rate)
        count = 0

        for seg in segments:
            combined += seg
            count += 1
            if count % flush_interval == 0:
                combined.export(temp_wav, format="wav")
                combined = AudioSegment.from_file(temp_wav, format="wav")
                combined = combined[-30000:]

        if count == 0:
            self._cleanup()
            return ""

        combined.export(temp_wav, format="wav")

        if output_path.endswith(".mp3"):
            AudioSegment.from_file(temp_wav, format="wav").export(
                output_path, format="mp3", bitrate="48k"
            )
        else:
            import shutil
            shutil.copy(temp_wav, output_path)

        self._cleanup()
        return output_path

    def _cleanup(self):
        """Remove temporary directory and all chunk files."""
        import shutil
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
