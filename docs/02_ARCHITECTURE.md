# 02 — KIẾN TRÚC TỐI GIẢN

## V1

Browser
  -> Local/Colab FastAPI
  -> TTS Adapter
  -> Engine
  -> WAV
  -> Browser

Không Redis.
Không database.
Không object storage bắt buộc.

## Các tầng

1. Text Normalizer
2. Vietnamese Text Frontend
3. Engine Adapter
4. Voice Reference Manager
5. Style Profile Manager
6. TTS Engine
7. Post-processing
8. Evaluation

## Adapter contract

Tất cả engine phải có cùng interface khái niệm:

generate(
    text,
    reference_audio,
    reference_text,
    style_profile,
    options
) -> wav_path

Engine implementations:
- F5TTSAdapter
- GPTSoVITSAdapter
- OpenVoiceAdapter (optional benchmark only)

Không copy source code của engine vào project. Clone repo vào thư mục vendor/ hoặc cài dependency theo license; wrapper nằm trong app.

## V2
Nếu V1 đạt chất lượng:
Browser -> FastAPI -> selected engine -> WAV.

## V3
Nếu cần fine-tuning:
Dataset -> metadata -> training/fine-tuning -> evaluation -> selected checkpoint.

Chỉ fine-tune sau benchmark zero-shot.
