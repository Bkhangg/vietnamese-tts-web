"""
Download Piper TTS voices from HuggingFace.
Usage:
    python download_piper_voice.py              # list available voices
    python download_piper_voice.py en_US-amy     # download specific voice
    python download_piper_voice.py --list-en     # list English voices only
"""

import sys, os, json, urllib.request, tempfile, zipfile
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models" / "piper"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Common Piper voices (quality: medium recommended for balance)
AVAILABLE = {
    # English - US
    "en_US-lessac-medium": {"lang": "en-US", "quality": "medium", "desc": "US English Lessac (medium) [recommended]"},
    "en_US-ryan-medium": {"lang": "en-US", "quality": "medium", "desc": "US English Ryan (medium)"},
    "en_US-ryan-high": {"lang": "en-US", "quality": "high", "desc": "US English Ryan (high)"},
    "en_US-ryan-low": {"lang": "en-US", "quality": "low", "desc": "US English Ryan (low)"},
    "en_US-libritts_r-medium": {"lang": "en-US", "quality": "medium", "desc": "US English LibriTTS-R (medium)"},
    "en_US-kathleen-medium": {"lang": "en-US", "quality": "medium", "desc": "US English Kathleen (medium)"},
    "en_US-kathleen-high": {"lang": "en-US", "quality": "high", "desc": "US English Kathleen (high)"},
    "en_US-lessac-high": {"lang": "en-US", "quality": "high", "desc": "US English Lessac (high)"},
    "en_US-lessac-low": {"lang": "en-US", "quality": "low", "desc": "US English Lessac (low)"},
    # English - GB
    "en_GB-alan-medium": {"lang": "en-GB", "quality": "medium", "desc": "GB English Alan (medium)"},
    "en_GB-alan-low": {"lang": "en-GB", "quality": "low", "desc": "GB English Alan (low)"},
    "en_GB-semaine-medium": {"lang": "en-GB", "quality": "medium", "desc": "GB English Semaine (medium)"},
    "en_GB-cori-high": {"lang": "en-GB", "quality": "high", "desc": "GB English Cori (high)"},
    "en_GB-cori-medium": {"lang": "en-GB", "quality": "medium", "desc": "GB English Cori (medium)"},
    # Other languages
    "de_DE-thorsten-medium": {"lang": "de-DE", "quality": "medium", "desc": "German Thorsten (medium)"},
    "de_DE-eva_k-x_low": {"lang": "de-DE", "quality": "x_low", "desc": "German Eva (x-low)"},
    "fr_FR-siwis-medium": {"lang": "fr-FR", "quality": "medium", "desc": "French Siwis (medium)"},
    "es_ES-davefx-medium": {"lang": "es-ES", "quality": "medium", "desc": "Spanish Davefx (medium)"},
}

# Remove invalid entry
AVAILABLE.pop("ja_JP-朝日", None)


def list_voices(filter_lang=None):
    print(f"{'Name':<25} {'Lang':<8} {'Quality':<8} Description")
    print("-" * 70)
    for name, info in sorted(AVAILABLE.items()):
        if filter_lang and filter_lang not in name:
            continue
        print(f"{name:<25} {info['lang']:<8} {info['quality']:<8} {info.get('desc', '')}")


def _hf_path(voice_info):
    """Build HuggingFace relative path from voice info dict."""
    lang = voice_info["lang"]                     # "en-US"
    quality = voice_info["quality"]               # "medium"
    name = voice_info["name"]                     # "lessac"
    lang_full = lang.replace("-", "_")
    lang_short = lang.split("-")[0]
    fname = f"{lang_full}-{name}-{quality}.onnx"
    return f"{lang_short}/{lang_full}/{name}/{quality}/{fname}"


def download_voice(voice_name):
    if voice_name not in AVAILABLE:
        print(f"Voice '{voice_name}' not found. Available voices:")
        list_voices()
        return

    info = AVAILABLE[voice_name]

    # Derive the name part by stripping lang and quality from voice_name
    # voice_name format: {lang}_{name}-{quality}
    lang_hf = info["lang"].replace("-", "_")      # "en_US"
    quality = info["quality"]                     # "medium"
    prefix = lang_hf + "-"
    suffix = "-" + quality
    name = voice_name
    if name.startswith(prefix):
        name = name[len(prefix):]
    if name.endswith(suffix):
        name = name[:-len(suffix)]
    voice_info = {**info, "name": name}

    hf_rel = _hf_path(voice_info)
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    base_dir = hf_rel.rsplit("/", 1)[0]
    files = [f"{voice_name}.onnx", f"{voice_name}.onnx.json"]

    for fname in files:
        url = f"{base_url}/{base_dir}/{fname}"
        dest = MODELS_DIR / fname
        if dest.exists():
            print(f"  EXISTS: {fname}")
            continue
        print(f"  DOWNLOAD: {fname}...")
        try:
            urllib.request.urlretrieve(url, dest)
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"    OK ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"    FAILED: {e}")
            if dest.exists():
                dest.unlink()
            return

    print(f"\nDone! Voice '{voice_name}' saved to {MODELS_DIR}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python download_piper_voice.py                — list voices")
        print("  python download_piper_voice.py en_US-amy      — download voice")
        print("  python download_piper_voice.py --list-en       — list English voices\n")
        list_voices()
    elif sys.argv[1] == "--list-en":
        list_voices(filter_lang="en")
    else:
        download_voice(sys.argv[1])
