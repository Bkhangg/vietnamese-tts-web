"""
Main controller: orchestrates text analysis, silence generation,
and TTS engine integration for Vietnamese.
"""

import logging
from typing import Dict, List, Optional, Generator

from pydub import AudioSegment

from .config import load_config
from .text_analyzer import split_into_phrases
from .silence_engine import SilenceEngine

log = logging.getLogger(__name__)

# Default pause table (ms) — used when config is missing a type
_FALLBACK_PAUSE = {
    "comma": 150,
    "semicolon": 250,
    "colon": 250,
    "period": 400,
    "question": 400,
    "exclamation": 450,
    "ellipsis": 600,
    "paragraph": 800,
    "sentence_break": 50,
    "quotation_start": 200,
    "quotation_end": 300,
    "parenthesis_start": 100,
    "parenthesis_end": 150,
    "dash": 200,
}


class VietnameseTTSController:
    """
    High-level controller that:
      1. Analyzes text → segments with pause types
      2. Looks up pause durations from the active profile
      3. Generates silence + audio for each segment
      4. Stitches everything into a final file
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        mode: str = "story",
        sample_rate: int = 22050,
    ):
        self.config = load_config(config_path)
        self.mode = mode
        self.sample_rate = sample_rate
        self.silence = SilenceEngine(sample_rate=sample_rate)
        self._tts_callback = None

    @property
    def profile(self) -> Dict[str, int]:
        """Active pause profile for the current mode."""
        return self.config["modes"].get(self.mode, _FALLBACK_PAUSE)

    def get_pause(self, seg_type: str, prev_type: str = "") -> int:
        """
        Return pause duration in ms for a given segment type.
        Applies contextual adjustments:
          - Longer pause after paragraph vs. within sentence
          - Speed variance jitter for naturalness
        """
        base = self.profile.get(seg_type, _FALLBACK_PAUSE.get(seg_type, 200))

        if prev_type == "paragraph" and seg_type != "paragraph":
            base = int(base * 0.85)

        import random
        variance = self.profile.get("speed_variance", 0.05)
        jitter = random.uniform(-base * variance, base * variance)
        return max(10, int(base + jitter))

    def build_segments(
        self, text: str, tts_audio_map: Dict[str, str] = None
    ) -> Generator[AudioSegment, None, None]:
        """
        Yield AudioSegments ready for concatenation.

        tts_audio_map: optional dict mapping segment text → pre-rendered WAV path.
                       If None, you must call .set_tts_callback() beforehand.
        """
        phrases = split_into_phrases(text)
        prev_type = "paragraph"

        callback = getattr(self, "_tts_callback", None)

        for phrase_text, seg_type in phrases:
            pause_ms = self.get_pause(seg_type, prev_type)

            if phrase_text and callback:
                audio_path = callback(phrase_text)
                if audio_path:
                    yield AudioSegment.from_file(audio_path, format="wav")

            if pause_ms > 0:
                yield self.silence.make_silence(pause_ms)

            prev_type = seg_type

    def _tts_callback(self, text: str) -> Optional[str]:
        """Placeholder — override via .set_tts_callback()."""
        return None

    def set_tts_callback(self, fn):
        """
        Set a callable(text) → path_to_wav that the controller
        will invoke for each phrase.  The callback should return
        a WAV file path or None.
        """
        self._tts_callback = fn

    def process_text(
        self,
        text: str,
        output_path: str,
        tts_callback=None,
        stream: bool = False,
    ) -> str:
        """
        Full pipeline: analyze → generate silence → stitch → write.

        Args:
            text: Vietnamese text to process.
            output_path: .wav or .mp3 output file.
            tts_callback: optional; if provided, calls this for each phrase.
            stream: use streaming mode for very long texts.

        Returns:
            Path to the generated audio file.
        """
        if tts_callback:
            self.set_tts_callback(tts_callback)

        if stream:
            return self.silence.stitch_stream(
                self.build_segments(text), output_path
            )
        else:
            return self.silence.stitch_to_file(
                self.build_segments(text), output_path
            )

    def list_modes(self) -> List[str]:
        return list(self.config["modes"].keys())

    def set_mode(self, mode: str):
        if mode in self.config["modes"]:
            self.mode = mode
        else:
            raise ValueError(f"Unknown mode: {mode}. Available: {self.list_modes()}")
