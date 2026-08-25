# 11 — CHẨN ĐOÁN LỖI

## Model không chạy
Kiểm tra:
- Python version
- PyTorch/CUDA
- VRAM
- model path
- dependency

## Đọc sai tiếng Việt
Không vội đổi model.
Kiểm tra:
- normalization
- transcript
- phoneme/G2P
- dấu câu
- reference language

## Giọng không giống
Kiểm tra:
- reference quality
- speaker dataset
- reference duration
- engine
- fine-tuning

## Giọng giống nhưng âm điệu sai
Kiểm tra:
- style reference
- pause
- duration
- pitch
- style strength

## Text 5000 ký tự lỗi
Chunk theo câu/dấu câu.
Không cắt giữa từ nếu tránh được.
Ghép WAV bằng sample-rate thống nhất.

## Antigravity sửa lung tung
Dừng.
Đọc STATE.md.
Chạy test.
Chỉ sửa lỗi được tái hiện.
Không refactor lớn trong cùng một bước.
