"""
Example: using VietnameseTTSController with Edge TTS.

Run from the parent directory:
    python viet_tts_controller/example.py
"""

import sys, os, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 1. Import ---
from viet_tts_controller import VietnameseTTSController
from viet_tts_controller.config import dump_default_config
from viet_tts_controller.text_analyzer import split_into_phrases

# --- 2. Dump default config for editing ---
dump_default_config("my_profiles.json")
print("Default config written to my_profiles.json — edit and reload.")

# --- 3. Initialize controller ---
ctrl = VietnameseTTSController(mode="story")
print(f"Available modes: {ctrl.list_modes()}")

# --- 4. Sample Vietnamese text ---
sample_text = (
    "Trời mùa thu Hà Nội, xanh như một tấm kính không một gợn mây.\n"
    "Gió heo may thổi nhẹ qua từng con phố, mang theo hương cốm mới và hoa sữa nồng nàn.\n\n"
    "Lan bước đi trên con đường quen thuộc. Cô dừng lại trước quán cà phê nhỏ góc phố,\n"
    'nơi có những chiếc bàn gỗ đơn sơ và những chậu hoa giấy tím biếc.\n\n'
    '"Em có muốn một ly cà phê sữa đá không?" — giọng anh trầm ấm, quen thuộc đến nao lòng.\n'
    "Lan mỉm cười, gật đầu. Cô kéo chiếc ghế ra ngồi xuống, cảm nhận từng khoảnh khắc bình yên."
)

# --- 5A. Quick test: just analyse pause structure ---
print("=" * 60)
print("Phân tích ngắt nghỉ:")
phrases = split_into_phrases(sample_text)
for text, seg_type in phrases[:12]:
    pause_ms = ctrl.get_pause(seg_type)
    label = (text[:50] + "...") if len(text) > 50 else text
    print(f"  [{seg_type:>15}] ({pause_ms:>4}ms) {label}")

# --- 5B. Full TTS run (requires edge-tts) ---
def edge_tts_callback(text: str) -> str:
    import asyncio, edge_tts, uuid
    path = os.path.join(tempfile.gettempdir(), f"phrase_{uuid.uuid4().hex}.wav")
    async def _gen():
        c = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural", rate="+0%", pitch="+0Hz", volume="+0%")
        await c.save(path)
    asyncio.run(_gen())
    return path

print("=" * 60)
print("Đang tạo audio với Edge TTS (chế độ story)...")
output = ctrl.process_text(
    sample_text, "output_story.mp3",
    tts_callback=edge_tts_callback, stream=True,
)
print(f"Đã tạo: {output}")

# --- 6. Switch to news mode ---
ctrl.set_mode("news")
short_text = ("Hôm nay, thị trường chứng khoán tăng mạnh. "
              "Các chỉ số chính đều ở mức cao nhất trong năm.")
output2 = ctrl.process_text(short_text, "output_news.mp3",
                             tts_callback=edge_tts_callback, stream=True)
print(f"Đã tạo (news): {output2}")

# --- 7. Silence-only timing track ---
ctrl.set_mode("audiobook")
timing = ctrl.process_text(sample_text, "timing_audiobook.wav")
print(f"Bản nhạc timing (silence): {timing}")
