# 01 — YÊU CẦU ĐÃ DUYỆT

## 1. Phạm vi
Đây là Personal Vietnamese TTS Studio, không phải SaaS.

## 2. Input
- Văn bản tiếng Việt.
- Mục tiêu khoảng 5.000 ký tự/lần.
- Hệ thống phải tự chia đoạn an toàn nếu vượt giới hạn engine.

## 3. Output
- WAV là master.
- MP3 là output phụ nếu cần.
- Audio phải nghe trực tiếp trên web.

## 4. Voice
- 1 speaker chính.
- Reference audio do người dùng cung cấp.
- Dataset có thể gồm nhiều recording của cùng người.
- Chất lượng recording ưu tiên cao hơn số lượng.

## 5. Style
Tối đa 3:
- neutral
- serious/calm
- storytelling

Style profile phải tách khỏi identity của speaker ở mức kiến trúc.

## 6. Tần suất
2–3 lần/ngày. Không cần queue.

## 7. Chi phí
Mục tiêu 0 đồng:
- open-source software
- local GPU nếu có
- Google Colab Free khi phù hợp
- Google Drive cho dữ liệu cá nhân nếu cần
Không dùng API thương mại trả phí trong core path.

## 8. Không làm
- multi-user
- billing
- subscription
- public API
- Redis/Celery
- PostgreSQL
- S3/CDN
- enterprise auth
- analytics
- community accounts

## 9. Mục tiêu chất lượng
Không coi 90–95% là một metric tuyệt đối.
Nghiệm thu bằng:
- pronunciation accuracy
- speaker similarity
- naturalness
- prosody/style similarity
- long-text stability
- human blind A/B listening

## 10. An toàn
Chỉ clone giọng mà người dùng sở hữu hoặc được phép sử dụng.
