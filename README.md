# Vietnamese TTS Web

Ứng dụng Text-to-Speech tiếng Việt với giao diện web, hỗ trợ **Microsoft Neural** và **Google TTS**.

<!-- Bạn có thể thêm ảnh chụp màn hình vào thư mục images/ và link ở đây -->

## Tính năng

### Giọng đọc
- **Microsoft Neural**: Hoài My (Nữ) và Nam Minh (Nam) — giọng AI tự nhiên, hỗ trợ chỉnh tốc độ, cao độ, âm lượng
- **Google TTS**: Giọng ổn định, nhẹ, không cần cấu hình

### Chế độ đọc
| Chế độ | Mô tả |
|--------|-------|
| **Bình thường** | Đọc toàn bộ văn bản với một giọng đều |
| **Sinh động** | Tự động chia câu, lên giọng ở câu hỏi, nhấn mạnh câu cảm thán, cao độ biến thiên tự nhiên |

### Giao diện
- Theme **sáng/tối** (nút 🌙/☀️ góc phải)
- Lịch sử 20 đoạn gần nhất (lưu localStorage), click để phát lại
- Nút **Xóa lịch sử**
- Tải file **MP3** sau khi phát

### Tiện ích
- **Đọc file .txt**: nhấn "Mở file" để tải văn bản
- **Text mẫu**: chào hỏi, thời tiết, giới thiệu, công nghệ
- **Phím tắt**:
  - `Enter` — Phát
  - `Shift + Enter` — Xuống dòng
  - `Ctrl + ↑ / ↓` — Tăng/giảm tốc độ

## Cài đặt

### Yêu cầu
- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) (cho chế độ Sinh động)

### Các bước

```bash
git clone https://github.com/Bkhangg/vietnamese-tts-web.git
cd vietnamese-tts-web

pip install edge-tts flask gtts pydub

python app.py
```

Mở trình duyệt tại **http://127.0.0.1:5000**

> **Lưu ý**: edge-tts và gTTS cần kết nối internet để hoạt động.

## API

### `POST /speak`

```json
{
  "text": "Xin chào Việt Nam!",
  "engine": "microsoft",
  "voice": "female",
  "rate": "0",
  "pitch": "0",
  "volume": "0",
  "lively": false
}
```

| Tham số | Kiểu | Mặc định | Mô tả |
|---------|------|----------|-------|
| `text` | string | — | Văn bản cần đọc |
| `engine` | string | `microsoft` | `microsoft` hoặc `google` |
| `voice` | string | `female` | `female` (Hoài My) / `male` (Nam Minh) |
| `rate` | string | `0` | Tốc độ (-50 đến 50) |
| `pitch` | string | `0` | Cao độ (-50 đến 50) |
| `volume` | string | `0` | Âm lượng (-50 đến 50) |
| `lively` | bool | `false` | Chế độ sinh động (chỉ Microsoft) |

Trả về file MP3.

## Công nghệ

- **Backend**: Python Flask
- **TTS Engine**: [edge-tts](https://github.com/rany2/edge-tts) + [gTTS](https://github.com/pndurette/gTTS)
- **Audio**: pydub + ffmpeg
- **Frontend**: HTML/CSS/JS thuần
