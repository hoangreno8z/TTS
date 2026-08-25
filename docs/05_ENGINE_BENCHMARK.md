# 05 — BENCHMARK ENGINE

## Engine bắt buộc benchmark
1. F5-TTS
2. GPT-SoVITS

OpenVoice chỉ benchmark bổ sung nếu cần style/rhythm control.

## Nguyên tắc
Cùng:
- reference audio
- reference transcript
- 20 câu tiếng Việt
- seed/options được ghi lại khi engine hỗ trợ
- output WAV

## Bộ 20 câu
Phải gồm:
- câu ngắn
- câu dài
- câu hỏi
- câu cảm thán
- số
- ngày tháng
- tên riêng
- từ có hỏi/ngã
- câu nhiều dấu phẩy
- đoạn văn 500–1000 ký tự

## Chấm điểm
Mỗi engine:
- Pronunciation 0–10
- Speaker similarity 0–10
- Naturalness 0–10
- Prosody 0–10
- Stability 0–10
- Speed/VRAM 0–10

Không chọn engine vì GitHub stars.

## Human blind test
Tên file phải được random hóa.
Người nghe không biết engine nào tạo file.
