# 09 — BẢO MẬT VÀ QUYỀN GIỌNG

## Nguyên tắc
- Chỉ dùng voice có quyền sử dụng.
- Không public reference audio.
- Không commit audio cá nhân vào Git.
- Không commit model weights.
- Không commit .env.
- Không ghi API key vào code.
- Local-only mặc định.

## Nếu mở endpoint tạm thời
- bind localhost nếu không cần public
- nếu cần tunnel, dùng URL tạm thời
- tắt tunnel sau khi xong
- không lưu token trong frontend
- không cho phép arbitrary file paths
- validate file extension + MIME + size

## Data retention
Mặc định:
- input text chỉ lưu nếu người dùng chủ động lưu
- output nằm trong outputs/
- có nút xóa
