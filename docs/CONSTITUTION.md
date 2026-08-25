# HIẾN PHÁP DỰ ÁN LAPQUE PERSONAL VIETNAMESE TTS (10 LOCKS)

```text
═════════════════════════════════════════════════════════════════════
          LAPQUE PERSONAL VIETNAMESE TTS — 10 PROJECT LOCKS
═════════════════════════════════════════════════════════════════════
```

1. **LOCK 01 — Vietnamese-First:**
   Mọi pipeline từ tiền xử lý, phân tách câu, tokenization, acoustic model đến hậu kiểm đều lấy tiếng Việt chuẩn dấu và chuẩn thanh điệu làm trọng tâm tối thượng.

2. **LOCK 02 — Reference Audio + Human-Verified Transcript:**
   Mọi quá trình Zero-Shot / Few-Shot Cloning bắt buộc phải đi kèm Cặp: `1 Reference Audio` + `1 Human-Verified Reference Transcript` do người dùng kiểm tra xác nhận. ASR chỉ là trợ lý dự thảo ban đầu, không phải nguồn chân lý cuối cùng.

3. **LOCK 03 — No F5-TTS Base As Vietnamese Engine By Assumption:**
   Không được dùng checkpoint F5-TTS Base quốc tế rồi giả định nó tự giải quyết tiếng Việt. Checkpoint được sử dụng bắt buộc phải có vocabulary/tokenizer và acoustic training phù hợp với tiếng Việt.

4. **LOCK 04 — No Mel/F0 Injection Into V1 Model Interface:**
   F5-TTS là kiến trúc Flow-Matching. Mel-spectrogram và F0 chỉ phục vụ cho chẩn đoán (Diagnostic / Visualization / Evaluation), không tự ý xây pipeline ép Mel/F0 vào interface của model ở V1.

5. **LOCK 05 — Independent 3-Dimensional Quality Evaluation:**
   Mọi chunk âm thanh sinh ra đều phải trải qua đánh giá độc lập trên 3 chiều:
   - Chiều 1: Vietnamese ASR + Text Diff (bắt lỗi chính tả, nuốt từ).
   - Chiều 2: Audio QA (clipping, silence, RMS, click detection).
   - Chiều 3: Speaker Similarity (embedding cosine distance).

6. **LOCK 06 — Finite Retry Policy (`max_retries_per_chunk: 3`):**
   Khi một chunk âm thanh không đạt chuẩn Quality Gate, hệ thống tự động sinh lại với jitter ngẫu nhiên tối đa 3 lần. Tuyệt đối không lặp vô tận.

7. **LOCK 07 — Failed Chunk = `NEEDS_REVIEW` + `[HOLD]`:**
   Nếu sau 3 lần thử lại vẫn không đạt, chunk bị gán trạng thái `status = NEEDS_REVIEW` và **TẠM DỪNG (HOLD)**. Tuyệt đối KHÔNG tự động đưa chunk lỗi vào Master Audio. UI phải cho người dùng 4 tùy chọn: `[Nghe thử đoạn lỗi]` `[Thử lại]` `[Chấp nhận]` `[Bỏ qua]`.

8. **LOCK 08 — No Commercial Paid API (Cam Kết 0 Đồng Tuyệt Đối):**
   Antigravity tuyệt đối không được tự ý chuyển sang ElevenLabs, Azure TTS, Google Cloud TTS hay bất kỳ API thương mại có phí nào. Dự án trung thành 100% với giải pháp mã nguồn mở và hạ tầng miễn phí (Google Colab GPU T4 On-demand + Vercel PWA).

9. **LOCK 09 — Independent Model & Checkpoint License Verification:**
   Mọi checkpoint, repo và dataset phải được xác minh và lưu vết giấy phép độc lập trong `MODEL_LICENSE.md`. Không được đánh đồng license của mã nguồn (MIT) với license của checkpoint tiền huấn luyện (CC-BY-NC hoặc license riêng của dataset).

10. **LOCK 10 — Benchmark Determines Production Engine:**
    Mọi model trong danh sách đều là Candidate Pool. Trọng số và engine chính thức được quyết định hoàn toàn dựa trên kết quả Benchmark thực nghiệm (Blind test & Audio quality test). Không tuyên bố trước bất kỳ engine nào là người chiến thắng.
