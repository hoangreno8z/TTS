# QUY CHUẨN QUALITY GATE 3 CHIỀU ĐỘC LẬP (3 INDEPENDENT QUALITY DIMENSIONS)

---

## 1. MỤC TIÊU
Bắt lỗi phát âm, nuốt chữ, sai thanh điệu, đứt đoạn âm thanh và bảo vệ chất lượng giọng nói đầu ra cho văn bản lên đến 5.000 ký tự.

---

## 2. KIẾN TRÚC 3 CHIỀU ĐÁNH GIÁ ĐỘC LẬP (PARALLEL EVALUATION)

```text
                     GENERATED CHUNK WAV
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
   DIMENSION 1:          DIMENSION 2:         DIMENSION 3:
     AUDIO QA           VIETNAMESE ASR     SPEAKER SIMILARITY
         │                    │                    │
  - Clipping check      - Transcribe with    - Extract Speaker
    (< -0.1 dBFS)         PhoWhisper/Whisper   Embedding (WavLM/
  - Local RMS check     - Normalize ASR text   ECAPA-TDNN)
  - Silence length      - Token & Text Diff  - Cosine Distance
  - Click / Glitch        (Lexical errors)     vs Reference
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                      QUALITY AGGREGATOR
                              │
                              ▼
                       DECISION ENGINE
```

---

## 3. CẤU HÌNH NGƯỠNG LINH HOẠT (CONFIGURABLE THRESHOLDS)

> [!IMPORTANT]
> **Không có một ngưỡng CER/WER/Speaker Similarity universal nào được hard-code trước benchmark.**
> Ngưỡng đánh giá được cấu hình theo từng profile môi trường:

```yaml
quality_gate:
  thresholds:
    cer_max: configurable          # Sẽ hiệu chỉnh sau Benchmark B
    wer_max: configurable          # Sẽ hiệu chỉnh sau Benchmark B
    speaker_similarity_min: configurable # Sẽ hiệu chỉnh sau Benchmark C
    audio_quality_min: configurable
  profile:
    development:
      cer_max: 0.10
      speaker_similarity_min: 0.70
      audio_quality_min: 0.60
    benchmark:
      cer_max: 0.03
      speaker_similarity_min: 0.85
      audio_quality_min: 0.85
    production:
      cer_max: 0.05
      speaker_similarity_min: 0.80
      audio_quality_min: 0.80
```

---

## 4. CHÍNH SÁCH XỬ LÝ LỖI: `RETRY <= 3` $\rightarrow$ `NEEDS_REVIEW` + `[HOLD]`

```text
               DECISION ENGINE
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
      PASS                        FAIL
        │                           │
        ▼                           ▼
ADAPTIVE BOUNDARY             RETRY CHUNK
    STITCHER             (Seed / Jitter perturb)
                                    │
                            ┌───────┴───────┐
                            │               │
                         Pass <= 3       Fail > 3
                            │               │
                            ▼               ▼
                        STITCHER      NEEDS_REVIEW
                                            │
                                            ▼
                                         [HOLD]
                                (Không tự động stitch)
                                            │
                                   UI CẢNH BÁO USER:
                                   [Nghe thử đoạn lỗi]
                                   [Thử lại thủ công]
                                   [Chấp nhận (Accept)]
                                   [Bỏ qua đoạn này]
```
