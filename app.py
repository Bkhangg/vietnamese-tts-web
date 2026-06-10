import asyncio
import json
import logging
import os
import re
import random
import tempfile
import unicodedata
import uuid
from pathlib import Path

from flask import Flask, request, send_file, render_template, jsonify
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

AUDIO_DIR = tempfile.gettempdir()
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
PIPER_DIR = MODELS_DIR / "piper"
VOICES = {
    "female": "vi-VN-HoaiMyNeural",
    "male": "vi-VN-NamMinhNeural",
}

ENGINES = {
    "edge": "Edge TTS (dễ dùng, giọng tự nhiên)",
    "google": "Google TTS (online)",
    "piper": "Piper TTS (offline, nhẹ)",
}

PIPER_VOICES = {}
_piper_models_scanned = False


def scan_piper_voices():
    global _piper_models_scanned, PIPER_VOICES
    if _piper_models_scanned:
        return PIPER_VOICES
    PIPER_VOICES.clear()
    if PIPER_DIR.is_dir():
        for f in PIPER_DIR.iterdir():
            if f.suffix == ".onnx":
                json_path = f.with_name(f.stem + ".onnx.json")
                if json_path.exists():
                    try:
                        with open(json_path, encoding="utf-8") as jf:
                            cfg = json.load(jf)
                        lang = cfg.get("language", {}).get("code", "en-US")
                        name = cfg.get("name", f.stem)
                        PIPER_VOICES[f.stem] = {"path": str(f), "config": str(json_path), "language": lang, "name": name}
                    except Exception:
                        pass
    _piper_models_scanned = True
    return PIPER_VOICES


scan_piper_voices()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt(val):
    i = int(val)
    return f"+{i}%" if i >= 0 else f"{i}%"


def fmt_pitch(val):
    i = int(val)
    return f"+{i}Hz" if i >= 0 else f"{i}Hz"


def split_sentences(text):
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]


def sentence_pitch(sentence, base_pitch):
    s = sentence.strip()
    offset = random.randint(15, 25) if s.endswith("?") else random.randint(10, 20) if s.endswith("!") else random.randint(-5, 8)
    return base_pitch + offset


def sentence_rate_offset(sentence):
    s = sentence.strip()
    return random.randint(-5, 5) if s.endswith("?") or s.endswith("!") else 0


def strip_vietnamese_diacritics(text):
    nfkd = unicodedata.normalize('NFD', text)
    result = []
    for c in nfkd:
        if unicodedata.category(c) == 'Mn':
            continue
        if c == '\u0111':
            result.append('d')
        elif c == '\u0110':
            result.append('D')
        else:
            result.append(c)
    return unicodedata.normalize('NFC', ''.join(result))


def normalize_for_piper(text):
    text = strip_vietnamese_diacritics(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[^\x20-\x7E\n]', '?', text)
    return text


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    piper_voices = {k: v["name"] for k, v in PIPER_VOICES.items()}
    return render_template("index.html", voices=VOICES, engines=ENGINES, piper_voices=piper_voices)


@app.route("/voices")
def get_voices():
    return jsonify(VOICES)


@app.route("/engines")
def get_engines():
    return jsonify(ENGINES)


@app.route("/piper-voices")
def get_piper_voices():
    return jsonify({k: v["name"] for k, v in scan_piper_voices().items()})


@app.route("/speak", methods=["POST"])
def speak():
    data = request.json
    text = data.get("text", "").strip()
    engine = data.get("engine", "edge")

    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400

    handlers = {
        "edge": _handle_edge,
        "google": _handle_google,
        "piper": _handle_piper,
    }
    handler = handlers.get(engine)
    if not handler:
        return jsonify({"error": f"Engine không hỗ trợ: {engine}"}), 400
    return handler(text, data)


# ---------------------------------------------------------------------------
# Edge TTS (Microsoft Neural)
# ---------------------------------------------------------------------------

def _handle_edge(text, data):
    voice = data.get("voice", "female")
    lively = data.get("lively", False)
    if lively:
        return _speak_edge_lively(text, voice, data)
    return _speak_edge(text, voice, data)


def _speak_edge(text, voice, data):
    rate = fmt(data.get("rate", "0"))
    pitch = fmt_pitch(data.get("pitch", "0"))
    volume = fmt(data.get("volume", "0"))
    voice_code = VOICES.get(voice, VOICES["female"])
    filepath = os.path.join(AUDIO_DIR, f"tts_{uuid.uuid4().hex}.mp3")

    async def _gen():
        import edge_tts
        from edge_tts.exceptions import NoAudioReceived
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice_code, rate=rate, pitch=pitch, volume=volume)
                await c.save(filepath)
                return
            except NoAudioReceived:
                log.warning(f"Edge TTS attempt {attempt + 1} failed")
                await asyncio.sleep(1)
        raise Exception("Không thể kết nối dịch vụ giọng nói sau 3 lần thử")

    try:
        asyncio.run(_gen())
    except Exception as e:
        return jsonify({"error": str(e)}), 503
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


def _speak_edge_lively(text, voice, data):
    base_rate = int(data.get("rate", "0"))
    base_pitch = int(data.get("pitch", "0"))
    volume = fmt(data.get("volume", "0"))
    voice_code = VOICES.get(voice, VOICES["female"])
    sentences = split_sentences(text)

    if not sentences:
        return jsonify({"error": "Văn bản rỗng"}), 400

    combined = AudioSegment.empty()

    for s in sentences:
        p = sentence_pitch(s, base_pitch)
        rate_off = sentence_rate_offset(s)
        r = base_rate + rate_off
        tmp = os.path.join(AUDIO_DIR, f"tmp_{uuid.uuid4().hex}.mp3")

        async def _gen_sentence(text=s, path=tmp, rate_str=fmt(r), pitch_str=fmt_pitch(p)):
            import edge_tts
            from edge_tts.exceptions import NoAudioReceived
            for attempt in range(3):
                try:
                    c = edge_tts.Communicate(text, voice_code, rate=rate_str, pitch=pitch_str, volume=volume)
                    await c.save(path)
                    return
                except NoAudioReceived:
                    await asyncio.sleep(1)
            raise Exception("Không thể kết nối")

        try:
            asyncio.run(_gen_sentence())
            seg = AudioSegment.from_mp3(tmp)
            combined += seg
        except Exception as e:
            log.warning(f"Câu thất bại: {e}")
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    if len(combined) == 0:
        return jsonify({"error": "Không tạo được âm thanh"}), 500

    filepath = os.path.join(AUDIO_DIR, f"tts_{uuid.uuid4().hex}.mp3")
    combined.export(filepath, format="mp3", bitrate="48k")
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


# ---------------------------------------------------------------------------
# Google TTS
# ---------------------------------------------------------------------------

def _handle_google(text, data):
    filepath = os.path.join(AUDIO_DIR, f"tts_{uuid.uuid4().hex}.mp3")
    try:
        from gtts import gTTS
        tts = gTTS(text, lang="vi")
        tts.save(filepath)
        return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"Lỗi Google TTS: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Piper TTS (offline, lightweight)
# ---------------------------------------------------------------------------

def _handle_piper(text, data):
    voice_id = data.get("piper_voice", "")
    if not voice_id or voice_id not in PIPER_VOICES:
        if PIPER_VOICES:
            voice_id = next(iter(PIPER_VOICES))
        else:
            return jsonify({"error": "Không tìm thấy giọng Piper nào. Hãy đặt file .onnx vào models/piper/"}), 400

    vinfo = PIPER_VOICES[voice_id]
    try:
        from piper import PiperVoice
        voice = PiperVoice.load(vinfo["path"], vinfo["config"], use_cuda=False)
    except Exception as e:
        return jsonify({"error": f"Lỗi tải giọng Piper: {str(e)}"}), 500

    wav_path = os.path.join(AUDIO_DIR, f"tts_{uuid.uuid4().hex}.wav")

    try:
        import wave
        audio_stream = voice.synthesize(normalize_for_piper(text))
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(voice.config.sample_rate)
            for chunk in audio_stream:
                wf.writeframes(chunk.audio_int16_bytes)
    except Exception as e:
        return jsonify({"error": f"Lỗi Piper synthesis: {str(e)}"}), 500

    mp3_path = wav_path.replace(".wav", ".mp3")
    try:
        AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate="48k")
    except Exception:
        mp3_path = wav_path

    return send_file(mp3_path, mimetype="audio/mpeg" if mp3_path.endswith(".mp3") else "audio/wav", as_attachment=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"TTS App running on http://localhost:{port}")
    print(f"Engines: {', '.join(ENGINES.keys())}")
    print(f"Piper voices: {list(PIPER_VOICES.keys())}")
    app.run(host="0.0.0.0", port=port, debug=True)
