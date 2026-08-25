# 00 — BÁO CÁO MÔI TRƯỜNG & PHẦN CỨNG (ENVIRONMENT AUDIT)

**Thời gian audit:** 2026-08-24  
**Script thực hiện:** `scripts/check_environment.py`

---

## 1. Thông Số Hệ Thống Thực Tế

| Thành phần | Trạng thái / Giá trị thực tế | Nhận xét |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10 (AMD64) | Môi trường phát triển cục bộ chuẩn |
| **Python** | Python 3.12.10 | Phiên bản Python 64-bit chính thức |
| **Pip** | Pip 26.1.2 | Đã cài đặt |
| **FFmpeg** | `NOT FOUND` (Chưa có trong PATH) | Cần cài đặt FFmpeg cục bộ để xử lý audio slicing/merging |
| **NVIDIA GPU** | Không tìm thấy `nvidia-smi` trong PATH | Không có card NVIDIA GPU rời cục bộ (hoặc chưa cấu hình driver) |
| **CUDA & cuDNN** | Không khả dụng trên máy local | - |
| **PyTorch** | Chưa cài đặt trong base Python | Sẽ tạo venv hoặc cài thư viện tối thiểu cho Phase text |
| **Dung lượng ổ đĩa** | Tổng: 110.96 GB \| Còn trống: 17.05 GB | Đủ cho code, metadata và audio dataset nhỏ |

---

## 2. Đánh Giá & Chiến Lược Triển Khai (Execution Strategy)

Theo đúng định hướng tại [docs/08_FREE_INFRA.md](file:///C:/Users/ADMIN/Desktop/LAPQUE_TTS_VIETNAMESE_ANTIGRAVITY/LAPQUE_TTS_VIETNAMESE_ANTIGRAVITY/docs/08_FREE_INFRA.md):

1. **Phần phát triển cục bộ (Local Development — 0 đồng):**
   - **Phase 2 (Audio Dataset):** Viết script chuẩn hoá audio, VAD, metadata index.
   - **Phase 3 (Vietnamese Text Pipeline):** Xây dựng bộ Normalizer tiếng Việt (số, ngày, tiền, ký tự, viết tắt) 100% bằng rule-based deterministic và chạy Unit tests đầy đủ trên CPU local.
   - **Phase 9 (Long Text 5000 ký tự):** Xây dựng module chunking văn bản và ghép nối WAV trên local.
   - **Phase 11 (FastAPI Backend) & Phase 12 (Web UI):** Chạy backend và frontend trực tiếp trên localhost.

2. **Phần cần GPU (AI Core Inference & Benchmark — 0 đồng):**
   - **Phase 4 (F5-TTS) & Phase 5 (GPT-SoVITS):** Do máy tính cục bộ không có NVIDIA GPU/CUDA, ta sẽ sử dụng **Google Colab Free Tier (NVIDIA T4 GPU 15GB VRAM)** để chạy benchmark 20 câu và inference AI Core.
   - Dự án sẽ chuẩn bị sẵn notebook / standalone script Colab tương thích tuyệt đối với cấu trúc adapter của hệ thống.

---

## 3. Khuyến Nghị Cho Người Dùng

1. **Cài đặt FFmpeg (Tuỳ chọn cho máy local):** Có thể tải FFmpeg từ https://ffmpeg.org/ và thêm vào PATH của Windows nếu muốn cắt ghép audio trực tiếp trên máy.
2. **Google Colab:** Sẵn sàng tài khoản Google Drive để lưu trữ checkpoint và audio benchmark khi đến Phase 4 và 5.
