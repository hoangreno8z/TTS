# 07 — QUY TRÌNH FINE-TUNING F5-TTS CHO GIỌNG CÁ NHÂN (PHASE 10)

## 1. Khi Nào Cần Fine-Tuning?
- Khi tổng hợp Zero-shot chưa đạt độ tương đồng mong muốn về phát âm phương ngữ hoặc âm sắc đặc trưng.
- Khi người dùng đã chuẩn bị sẵn bộ dữ liệu âm thanh mẫu (tối thiểu 10–30 phút ghi âm sạch, không tạp âm, đã qua cắt lát 3–10s và transcript chính xác ở Phase 2).

---

## 2. Các Bước Thực Hiện Trên Google Colab (0 Đồng — T4 GPU)

### Bước 1: Chuẩn bị Dữ liệu
1. Thu thập và chuẩn hóa dữ liệu từ `data/voice/` và `data/metadata/metadata.csv`.
2. Phân tách tập huấn luyện (Train: 85%) và tập kiểm tra (Validation: 15%) độc lập.

### Bước 2: Nạp Checkpoint Cơ sở & Cấu hình Fine-tuning
- Khởi động Google Colab với runtime T4 GPU (Free Tier).
- Sử dụng checkpoint tiếng Việt hoặc upstream base:
  - Base: `F5TTS_Base` (DiT 1.2M steps).
  - Batch size: 4–8 (vừa vặn trong 15GB VRAM T4).
  - Learning rate: $1 \times 10^{-5}$ (tinh chỉnh nhẹ, tránh làm hỏng khả năng phát âm gốc).
  - Số bước huấn luyện: 5.000 – 15.000 steps.

### Bước 3: Lưu trữ & Đánh giá Lại (Re-evaluation)
1. Tự động lưu checkpoint tốt nhất dựa trên Validation Loss vào Google Drive.
2. Sinh lại đúng 20 câu kiểm thử tiêu chuẩn (`benchmark/benchmark_sentences.json`).
3. Thực hiện Blind Test A/B đối chiếu giữa mô hình Zero-shot ban đầu và mô hình Fine-tuned.
4. Chỉ cập nhật checkpoint mới vào `config/engines.yaml` khi điểm số thực tế cải thiện vượt trội.
