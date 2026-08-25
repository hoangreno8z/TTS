"""PHASE A: PROOF OF VOICE COLAB SCRIPT.
Loads Vietnamese F5-TTS / Vi-F5-TTS, takes 1 Reference WAV + 1 Verified Transcript,
and generates the 20 Benchmark evaluation sentences on Free T4 GPU.
"""

# Cell 1: Install Dependencies
# !pip install -q git+https://github.com/SWivid/F5-TTS.git soundfile librosa huggingface_hub

import os
import sys
import time
import torch
import soundfile as sf
from f5_tts.model import DiT
from f5_tts.infer.utils_infer import load_model, load_vocoder, infer_process

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"-> Thiết bị GPU: {device.upper()} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

# 1. Tải Vocos Vocoder
vocoder = load_vocoder(vocoder_name="vocos", is_local=False)

# 2. Tải Checkpoint F5-TTS Tiếng Việt chuyên biệt (Vietnamese Vocab & DiT)
print("-> Đang nạp mô hình F5-TTS Tiếng Việt...")
model_f5 = load_model(
    model_cls=DiT,
    model_cfg=dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
    ckpt_path="hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors", # Thay thế bằng Vietnamese Checkpoint
    mel_spec_type="vocos",
    vocab_file="",
    device=device
)
print("-> Đã nạp xong mô hình!")

# 20 Câu Benchmark Tiêu Chuẩn Phase A
BENCHMARK_20 = [
    "Xin chào bạn, tôi là trợ lý giọng nói tiếng Việt cá nhân của bạn.",
    "Hôm nay là ngày 24 tháng 8 năm 2026, thời tiết tại Hà Nội rất trong lành.",
    "Tôi tên là Nguyễn Huy Hoàng, rất vui được đồng hành cùng bạn trong dự án này.",
    "Mỗi buổi sáng, việc đọc sách và rèn luyện thể thao giúp tinh thần luôn sảng khoái.",
    "Nguyễn Hoài Nam vừa hoàn thành thủ tục xuất nhập khẩu hàng hóa tại cảng Hải Phòng.",
    "Con đường quanh co uốn khúc ngoằn ngoèo đưa chúng tôi đến một thung lũng rực rỡ.",
    "Dưới ánh nắng ban mai, những giọt sương mai đọng trên cành lá lung linh kỳ ảo.",
    "Nghệ thuật điêu khắc gỗ truyền thống đòi hỏi sự tỉ mỉ, kiên nhẫn và đôi bàn tay khéo léo.",
    "Bạn hãy giữ vững ý chí, vượt qua mọi nỗi gian truân và khó khăn thử thách.",
    "Kỷ niệm xưa cũ bỗng ùa về trong một buổi chiều thu yên ả và lộng gió.",
    "Sự hiểu biết sâu rộng cùng lòng kiên nhẫn sẽ mở ra những cánh cửa mới.",
    "Những bãi cỏ xanh mướt trải dài vô tận dưới chân dãy núi hùng vĩ.",
    "Dự án đạt tăng trưởng 15.5% trong quý 3 năm 2026 với tổng doanh thu 120 tỷ đồng.",
    "Các chuyên gia công nghệ AI tại TP. Hồ Chí Minh vừa công bố báo cáo mới.",
    "Nhiệt độ trung bình tại khu vực miền Trung dao động từ 28 đến 34 độ C.",
    "Quy trình kiểm định chất lượng được thực hiện nghiêm ngặt qua 3 giai đoạn độc lập.",
    "Tuyệt vời quá! Chúng ta đã hoàn thành xuất sắc mục tiêu đề ra rồi!",
    "Bạn có tin rằng công nghệ giọng nói AI có thể học được cảm xúc của con người không?",
    "Hãy lắng nghe thật kỹ từng nhịp thở của tự nhiên, bạn sẽ cảm nhận được sự bình yên.",
    "Chặng đường phía trước còn nhiều điều thú vị đang chờ đón chúng ta cùng khám phá."
]

def synthesize_phase_a(ref_audio: str, ref_transcript: str, output_dir: str = "phase_a_results"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 65)
    print(f"BAT DAU TONG HOP 20 CAU BENCHMARK")
    print(f"Ref Audio     : {ref_audio}")
    print(f"Ref Transcript: {ref_transcript}")
    print("=" * 65)

    for i, text in enumerate(BENCHMARK_20, 1):
        out_f = os.path.join(output_dir, f"cau_{i:02d}.wav")
        print(f"[{i:02d}/20] \"{text[:40]}...\"")
        wav, sr, _ = infer_process(
            ref_audio=ref_audio,
            ref_text=ref_transcript,
            gen_text=text,
            model_obj=model_f5,
            vocoder=vocoder,
            device=device
        )
        sf.write(out_f, wav, sr)
    print(f"\n-> HOAN THANH! 20 file audio da duoc luu tai thu muc: {output_dir}")

if __name__ == "__main__":
    # synthesize_phase_a("Loc-Dinh-Ky.mp3", "Transcript chính xác của file mẫu ở đây")
    pass
