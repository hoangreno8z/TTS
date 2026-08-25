# 03 — DATASET GIỌNG CÁ NHÂN

## Mục tiêu ban đầu
30–60 phút recording sạch là bộ thử nghiệm ban đầu.
Nếu chưa đủ, mở rộng lên 1–3 giờ hoặc hơn.

Không suy luận rằng 30–60 phút sẽ đảm bảo 95%. Nó chỉ là mốc thử nghiệm.

## Recording
Ưu tiên:
- WAV lossless
- mono
- 24 kHz hoặc 48 kHz
- ít noise
- không nhạc nền
- không reverb
- microphone/môi trường ổn định

MP3 vẫn có thể dùng để prototype nhưng nên chuyển sang WAV để xử lý.

## Pipeline
raw audio
 -> FFmpeg normalization
 -> VAD
 -> silence trimming
 -> quality checks
 -> segmentation
 -> ASR draft
 -> human transcript correction
 -> metadata
 -> train/inference set

## Cấu trúc
data/voice/
  neutral/
  serious/
  storytelling/

Mỗi segment nên ngắn, rõ câu, không chứa nhiều câu không liên quan.

## Reference inference
Ưu tiên reference rõ, ít nhiễu và ngắn. Với F5-TTS Vietnamese community pipeline, hướng dẫn hiện có khuyến nghị reference rõ và dưới 10 giây cho inference; đây là khuyến nghị của repo cộng đồng, không phải quy luật chung cho mọi model.

## Transcript
ASR chỉ tạo bản nháp.
Transcript cuối phải được kiểm tra.
Đặc biệt kiểm tra:
- thanh điệu
- số
- ngày tháng
- tên riêng
- chữ viết tắt
- dấu câu

## Metadata tối thiểu
file,text,speaker,style,quality_score
