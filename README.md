# Vietnamese TTS Web

Ứng dụng Text-to-Speech tiếng Việt với giao diện web, sử dụng giọng Neural AI của Microsoft Edge TTS.

## Tính năng

- **2 giọng đọc Neural**: Hoài My (Nữ) và Nam Minh (Nam) - chất giọng tự nhiên
- **Điều chỉnh**: tốc độ, cao độ (trầm/bổng), âm lượng
- **Tải file MP3**: sau khi phát, nhấn nút Tải để lưu về máy
- **Lịch sử**: tự động lưu 20 đoạn gần nhất (dùng localStorage), click để phát lại
- **Theme sáng/tối**: nhấn nút 🌙/☀️ góc phải
- **Đọc file .txt**: nhấn "Mở file" để đọc văn bản từ file
- **Phím tắt**:
  - `Enter` — Phát
  - `Shift + Enter` — Xuống dòng
  - `Ctrl + ↑/↓` — Tăng/giảm tốc độ
- **Text mẫu**: các nút chào hỏi, thời tiết, giới thiệu, công nghệ

## Cài đặt

### Yêu cầu

- Python 3.8+
- pip

### Các bước

```bash
# Clone repo
git clone https://github.com/Bkhangg/vietnamese-tts-web.git
cd vietnamese-tts-web

# Cài dependencies
pip install edge-tts flask

# Chạy app
python app.py
```

Mở trình duyệt tại **http://127.0.0.1:5000**

## Công nghệ

- **Backend**: Python Flask
- **TTS Engine**: [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge TTS neural voices
- **Frontend**: HTML/CSS/JS thuần

## API

### `POST /speak`

```json
{
  "text": "Xin chào Việt Nam",
  "voice": "female",
  "rate": "0",
  "pitch": "0",
  "volume": "0"
}
```

Trả về file MP3.
