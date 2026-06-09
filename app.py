import asyncio
import edge_tts
from edge_tts.exceptions import NoAudioReceived
from flask import Flask, request, send_file, render_template, jsonify
import tempfile
import os
import uuid
import logging

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
    voice = data.get("voice", "female")
    rate = fmt(data.get("rate", "0"))
    pitch = fmt_pitch(data.get("pitch", "0"))
    volume = fmt(data.get("volume", "0"))

    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400

    voice_code = VOICES.get(voice, VOICES["female"])
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    async def _generate():
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice_code, rate=rate, pitch=pitch, volume=volume)
                await communicate.save(filepath)
                return
            except NoAudioReceived:
                log.warning(f"Lần thử {attempt + 1} thất bại, đang thử lại...")
                await asyncio.sleep(1)
        raise NoAudioReceived("Không thể kết nối dịch vụ giọng nói sau 3 lần thử")

    try:
        asyncio.run(_generate())
    except NoAudioReceived as e:
        return jsonify({"error": str(e)}), 503

    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
