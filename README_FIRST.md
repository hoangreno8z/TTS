# LAPQUE PERSONAL TTS — TIẾNG VIỆT
## Bộ kế hoạch + prompt cho Google Antigravity

Mục tiêu:
- 1 người dùng duy nhất.
- Chỉ tiếng Việt.
- Khoảng 5.000 ký tự/lần.
- Khoảng 2–3 lần/ngày.
- 1 giọng chính.
- 2–3 style.
- Ưu tiên tối đa Voice Similarity và Vietnamese Pronunciation.
- Mục tiêu cảm nhận: giọng mới phải rất gần giọng mẫu; không tuyên bố "95%" như một chỉ số tuyệt đối.
- Ưu tiên 0 đồng: mã nguồn mở, chạy local hoặc Google Colab miễn phí khi có thể.
- Không xây SaaS, không billing, không multi-user, không production queue.

QUAN TRỌNG:
1. Không code UI trước khi AI Core benchmark xong.
2. Không tự viết lại F5-TTS/GPT-SoVITS. Dùng adapter/wrapper.
3. Không tải hoặc nhúng model/checkpoint vào Git repo.
4. Không hard-code token/API key.
5. Chỉ sử dụng voice mà người dùng có quyền sử dụng.
6. Mọi license của code, checkpoint, dataset/model phải được kiểm tra riêng.
7. Không hứa clone 100%; phải benchmark thực tế.
8. Khi gặp lỗi, sửa tối thiểu, không phá phần đang chạy.

Đọc theo thứ tự:
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08.
Sau đó dùng prompts/ANTIGRAVITY_MASTER_PROMPT.md cho Google Antigravity.
