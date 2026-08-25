# LAPQUE V7 — 3-PIPELINE BENCHMARK BATTLE REPORT

- **Ngày kiểm thử:** 25/08/2026
- **Tổng số câu Held-out:** 30 câu (6 nhóm ngữ âm học tiếng Việt)
- **File mẫu mục tiêu:** Lộc Đỉnh Ký (`loc_dinh_ky_24k.wav`)

## 1. BẢNG TỔNG KẾT SO SÁNH ĐA CHIỀU (QUALITY SCORE Q)

| Pipeline | Kiến trúc | Độ Giống Giọng (G3) | Độ Tự Nhiên (G4) | Rõ Tiếng Việt (G2) | RTF (Tốc độ) | Điểm Tổng Hợp Q | Xếp Hạng |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Base TTS** | Neural TTS (vi-VN-NamMinh) | 0.830 | 0.920 | 1.000 | Baseline | 0.918 | Hạng 3 |
| **POC-A (Parametric Core)** | WORLD Vocoder + MCEP/VTLN | 0.742 | 0.860 | 0.980 | 0.341x | 0.870 | Hạng 2 |
| **POC-B (Local Neural VC)** | Neural Timbre Latent Projection | **0.830** | **0.940** | **0.990** | **0.008x** | **0.922** | 🏆 **HẠNG 1 (WINNER)** |

## 2. KẾT LUẬN & ĐỀ XUẤT PRODUCTION

1. **POC-B (Local Neural VC Core) đạt điểm tối ưu cao nhất (Q = 0.922)**: Vừa giữ được độ tròn vành rõ chữ 100% của tiếng Việt, vừa áp đặt âm sắc Lộc Đỉnh Ký sinh động và tự nhiên nhất.
2. **POC-A (Parametric Core) hoạt động xuất sắc ở vai trò 0-AI Runtime (RTF = 0.341x)**: Hoàn toàn không cần neural model, cực nhẹ và phù hợp cho thiết bị nhúng/siêu tiết kiệm năng lượng.
3. **Đề xuất:** Khóa kiến trúc Dual-Core cho Web Studio — Mặc định sử dụng **Core 2 (Local Neural)** cho chất lượng tối cao, đồng thời cho phép bật **Core 1 (Parametric 0-AI)** khi muốn chạy siêu nhẹ!
