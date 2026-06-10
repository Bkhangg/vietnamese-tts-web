"""
Configuration management for Vietnamese TTS pause controller.
Supports multiple reading modes with customizable pause durations.
"""

import json
from pathlib import Path
from typing import Dict, Optional

DEFAULT_CONFIG_PATH = Path(__file__).parent / "profiles.json"

DEFAULT_PROFILES = {
    "news": {
        "description": "Đọc tin tức — rõ ràng, dứt khoát, nhịp nhanh",
        "comma": 120,
        "semicolon": 200,
        "colon": 200,
        "period": 350,
        "question": 380,
        "exclamation": 400,
        "ellipsis": 500,
        "paragraph": 700,
        "quotation_start": 150,
        "quotation_end": 250,
        "parenthesis_start": 100,
        "parenthesis_end": 150,
        "dash": 200,
        "sentence_break": 50,
        "speed_variance": 0.03,
    },
    "story": {
        "description": "Kể chuyện — chậm rãi, giàu cảm xúc",
        "comma": 200,
        "semicolon": 350,
        "colon": 300,
        "period": 500,
        "question": 550,
        "exclamation": 600,
        "ellipsis": 800,
        "paragraph": 1200,
        "quotation_start": 250,
        "quotation_end": 350,
        "parenthesis_start": 150,
        "parenthesis_end": 200,
        "dash": 300,
        "sentence_break": 80,
        "speed_variance": 0.08,
    },
    "audiobook": {
        "description": "Sách nói — chậm, tự nhiên, có ngắt nghỉ sâu",
        "comma": 250,
        "semicolon": 400,
        "colon": 350,
        "period": 600,
        "question": 650,
        "exclamation": 700,
        "ellipsis": 1000,
        "paragraph": 1500,
        "quotation_start": 300,
        "quotation_end": 400,
        "parenthesis_start": 200,
        "parenthesis_end": 250,
        "dash": 350,
        "sentence_break": 100,
        "speed_variance": 0.10,
    },
    "youtube": {
        "description": "YouTube — nhanh, gọn, giữ chân người xem",
        "comma": 100,
        "semicolon": 150,
        "colon": 150,
        "period": 250,
        "question": 280,
        "exclamation": 300,
        "ellipsis": 400,
        "paragraph": 500,
        "quotation_start": 100,
        "quotation_end": 150,
        "parenthesis_start": 80,
        "parenthesis_end": 100,
        "dash": 120,
        "sentence_break": 30,
        "speed_variance": 0.02,
    },
}


def load_config(path: Optional[str] = None) -> Dict:
    """
    Load profiles from JSON file, falling back to defaults.
    User-supplied values override defaults for easy customization.
    """
    config = {"modes": {k: dict(v) for k, v in DEFAULT_PROFILES.items()}}

    path = path or str(DEFAULT_CONFIG_PATH)
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for mode, values in user.get("modes", {}).items():
            if mode in config["modes"]:
                config["modes"][mode].update(values)
            else:
                config["modes"][mode] = values

    return config


def dump_default_config(path: str):
    """Write the default config to disk for user editing."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROFILES, f, ensure_ascii=False, indent=2)
