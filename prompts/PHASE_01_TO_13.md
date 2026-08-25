# PROMPT PHASES — COPY TỪNG PHASE

## PHASE 1
Đọc docs và audit môi trường. Không code TTS.

## PHASE 2
Xây audio preprocessing + metadata. Không train.

## PHASE 3
Xây Vietnamese normalizer + tests.

## PHASE 4
Tích hợp F5-TTS bằng adapter. Chạy benchmark.

## PHASE 5
Tích hợp GPT-SoVITS bằng adapter. Chạy benchmark.

## PHASE 6
Sinh blind-test package + report.

## PHASE 7
Chốt engine dựa trên benchmark.

## PHASE 8
Tạo 2–3 style profile.

## PHASE 9
Xử lý 5000 ký tự, chunk + merge.

## PHASE 10
Chỉ khi cần: fine-tune.

## PHASE 11
FastAPI local.

## PHASE 12
Next.js UI.

## PHASE 13
Vercel optional.

Mỗi phase phải kết thúc bằng STATE.md + test report.
