import asyncio
import edge_tts
import re
import random
from edge_tts.exceptions import NoAudioReceived
from flask import Flask, request, send_file, render_template, jsonify
import tempfile
import os
import uuid
import logging
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

VOICES = {
    "female": "vi-VN-HoaiMyNeural",
    "male": "vi-VN-NamMinhNeural",
}

AUDIO_DIR = tempfile.gettempdir()


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
    if s.endswith("?"):
        offset = random.randint(15, 25)
    elif s.endswith("!"):
        offset = random.randint(10, 20)
    else:
        offset = random.randint(-5, 8)
    return base_pitch + offset


def sentence_rate_offset(sentence):
    s = sentence.strip()
    if s.endswith("?") or s.endswith("!"):
        return random.randint(-5, 5)
    return 0


@app.route("/")
def index():
    return render_template("index.html", voices=VOICES)


@app.route("/voices")
def get_voices():
    return jsonify(VOICES)


@app.route("/speak", methods=["POST"])
def speak():
    data = request.json
    text = data.get("text", "").strip()
    engine = data.get("engine", "microsoft")
    voice = data.get("voice", "female")
    lively = data.get("lively", False)

    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400

    if engine == "google":
        return _speak_google(text)

    if lively:
        return _speak_microsoft_lively(text, voice, data)
    return _speak_microsoft(text, voice, data)


def _speak_google(text):
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    try:
        from gtts import gTTS
        tts = gTTS(text, lang="vi")
        tts.save(filepath)
        return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"Lỗi Google TTS: {str(e)}"}), 500


def _speak_microsoft(text, voice, data):
    rate = fmt(data.get("rate", "0"))
    pitch = fmt_pitch(data.get("pitch", "0"))
    volume = fmt(data.get("volume", "0"))
    voice_code = VOICES.get(voice, VOICES["female"])
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    async def _gen():
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice_code, rate=rate, pitch=pitch, volume=volume)
                await c.save(filepath)
                return
            except NoAudioReceived:
                log.warning(f"Lần thử {attempt + 1} thất bại, đang thử lại...")
                await asyncio.sleep(1)
        raise NoAudioReceived("Không thể kết nối dịch vụ giọng nói sau 3 lần thử")

    try:
        asyncio.run(_gen())
    except NoAudioReceived as e:
        return jsonify({"error": str(e)}), 503
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


def _speak_microsoft_lively(text, voice, data):
    base_rate = int(data.get("rate", "0"))
    base_pitch = int(data.get("pitch", "0"))
    volume = fmt(data.get("volume", "0"))
    voice_code = VOICES.get(voice, VOICES["female"])
    sentences = split_sentences(text)

    if not sentences:
        return jsonify({"error": "Văn bản rỗng"}), 400

    temp_files = []
    combined = AudioSegment.empty()

    for i, s in enumerate(sentences):
        p = sentence_pitch(s, base_pitch)
        rate_off = sentence_rate_offset(s)
        r = base_rate + rate_off
        rate_str = fmt(r)
        pitch_str = fmt_pitch(p)

        tmp = os.path.join(AUDIO_DIR, f"tmp_{uuid.uuid4().hex}.mp3")
        temp_files.append(tmp)

        async def _gen_sentence(text=s, path=tmp):
            for attempt in range(3):
                try:
                    c = edge_tts.Communicate(text, voice_code, rate=rate_str, pitch=pitch_str, volume=volume)
                    await c.save(path)
                    return
                except NoAudioReceived:
                    await asyncio.sleep(1)
            raise NoAudioReceived("Không thể kết nối")

        try:
            asyncio.run(_gen_sentence())
            seg = AudioSegment.from_mp3(tmp)
            combined += seg
        except Exception as e:
            log.warning(f"Câu {i+1} thất bại: {e}")
            continue
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    if len(combined) == 0:
        return jsonify({"error": "Không tạo được âm thanh"}), 500

    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    combined.export(filepath, format="mp3", bitrate="48k")
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
