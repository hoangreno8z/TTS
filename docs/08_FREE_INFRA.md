# 08 — HẠ TẦNG 0 ĐỒNG

## Ưu tiên 1: Local
Nếu máy có NVIDIA GPU:
- chạy engine local
- FastAPI local
- web local

## Ưu tiên 2: Google Colab Free
Dùng để:
- benchmark
- inference
- thử fine-tuning

Không coi Colab là production server.
Session có thể ngắt.

## Drive
Dùng Drive để giữ:
- dataset
- metadata
- checkpoints cá nhân
- outputs

Không commit voice/model vào Git.

## Vercel
Chỉ cần nếu muốn giao diện web từ xa.
Không chạy GPU TTS trên Vercel.

## Chi phí
Software path có thể 0 đồng.
GPU free không được đảm bảo liên tục.
Không cam kết "0 đồng vĩnh viễn" vì dịch vụ miễn phí có thể thay đổi chính sách.
