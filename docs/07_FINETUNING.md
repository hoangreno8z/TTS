# 07 — FINE-TUNING

Fine-tuning là bước sau benchmark, không phải bước đầu.

## Khi nào fine-tune?
- zero-shot pronunciation không đủ
- speaker identity chưa đủ gần
- style không ổn định
- dataset sạch đã sẵn sàng

## Không được làm
- train mù
- thay đổi nhiều biến cùng lúc
- không lưu checkpoint
- không benchmark trước/sau
- không biết license checkpoint

## Quy trình
1. Freeze bản zero-shot tốt nhất.
2. Backup dataset.
3. Chuẩn hóa metadata.
4. Chạy training/fine-tuning.
5. Tạo validation set không dùng trong training.
6. Generate cùng 20 câu benchmark.
7. Blind test.
8. Chỉ giữ checkpoint nếu thực sự tốt hơn.

## Cảnh báo
Community F5-TTS Vietnamese repos có pipeline fine-tuning, nhưng quy mô dữ liệu lớn được khuyến nghị trong các repo đó không đồng nghĩa người dùng cá nhân bắt buộc phải có 100+ giờ. Phải thử zero-shot và fine-tuning nhỏ trước.
