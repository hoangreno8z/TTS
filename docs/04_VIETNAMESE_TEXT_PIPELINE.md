# 04 — PIPELINE TIẾNG VIỆT

## Mục tiêu
TTS không được đọc sai số, dấu câu và thanh điệu vì frontend.

## Text normalization
Ví dụ:
"Ngày 24/8/2026, có 2 căn nhà."
-> dạng đọc tiếng Việt nhất quán.

Không tự ý đổi nội dung ngữ nghĩa.

## Quy tắc
- Giữ nguyên tên riêng khi không có rule đọc đặc biệt.
- Số phải có rule.
- Ngày/tháng/năm phải có rule.
- Phần trăm/tiền tệ phải có rule.
- URL/email phải có rule.
- Dấu câu ảnh hưởng pause.
- Không dùng LLM làm bộ G2P duy nhất.
- Mọi rule phải deterministic và có test.

## Test suite
Tạo test cho:
1. số
2. ngày
3. tiền
4. phần trăm
5. viết tắt
6. dấu hỏi/ngã
7. tên riêng
8. câu dài
9. dấu hai chấm
10. ngoặc
