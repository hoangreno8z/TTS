# 06 — STYLE ENGINE

## Chỉ 3 style
neutral
serious
storytelling

## V1
Không xây một neural Style Encoder riêng nếu engine đã có reference/style mechanism.
Tạo StyleProfile ở tầng ứng dụng.

Mỗi profile chứa:
- reference_audio
- reference_text
- target_speed
- pause preference
- optional pitch/prosody controls supported by engine
- notes

## Mục tiêu
Voice identity không được thay đổi mạnh khi đổi style.

So sánh:
A = voice only
B = voice + style

Nếu B làm mất speaker identity thì giảm style strength.

## V2
Chỉ khi benchmark chứng minh cần thiết mới nghiên cứu Style Encoder/Prosody Encoder riêng.
