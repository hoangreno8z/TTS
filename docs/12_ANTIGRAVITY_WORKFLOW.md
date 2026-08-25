# 12 — WORKFLOW CHO GOOGLE ANTIGRAVITY

AI phải làm từng phase, không nhảy phase.

Mỗi phase:
1. Đọc docs.
2. Kiểm tra trạng thái hiện tại.
3. Lập danh sách file sẽ sửa.
4. Sửa tối thiểu.
5. Chạy test.
6. Báo cáo.
7. Chờ phase tiếp theo nếu chưa được yêu cầu.

Không được:
- xóa code đang chạy chỉ vì thích kiến trúc khác
- thay engine mà không benchmark
- tự tải checkpoint không rõ license
- tạo API trả phí
- thêm database/Redis nếu không cần
- thêm dependency nặng không có lý do
- giả vờ tính được 95% similarity

STATE.md phải ghi:
- phase hiện tại
- engine
- model path
- Python/CUDA
- test đã pass
- test fail
- việc tiếp theo
