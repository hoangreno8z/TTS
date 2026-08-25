"""PHASE A: VI-F5-TTS VIETNAMESE CHECKPOINT BENCHMARK (COLAB GPU T4).
Model               : danhtran2mind/Vi-F5-TTS (Trained on vin100h Vietnamese dataset)
Vocab               : Vi-F5-TTS/vocab.txt (Native Vietnamese phonemes & diacritics)
Reference Audio     : loc-dinh-ky.wav (18.69s)
Reference Transcript: "Những lời lẽ đê tiện như vậy mà ngươi cũng nói ra được hay sao hả?"
Output              : 20 Crystal-Clear Vietnamese Sentences + In-Notebook Player + ZIP Download
"""

# Cell 1: Install Dependencies & Download Vietnamese Model
# !pip install -q git+https://github.com/SWivid/F5-TTS.git soundfile librosa ipywidgets huggingface_hub

import os
import sys
import time
import torch
import soundfile as sf
from IPython.display import Audio, display
from huggingface_hub import snapshot_download
from f5_tts.model import DiT
from f5_tts.infer.utils_infer import load_model, load_vocoder, infer_process

device = "cuda" if torch.cuda.is_available() else "cpu"
print("=" * 65)
print("   LAPQUE TTS — PHASE A: VIETNAMESE VI-F5-TTS (VIN100H) BENCHMARK")
print("=" * 65)
print(f"-> Thiet bi GPU: {device.upper()} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

# 1. Tải bộ trọng số và từ điển tiếng Việt Vi-F5-TTS chính thức
print("\n-> Dang tai mo hinh Tieng Viet chuyen biet (Vi-F5-TTS vin100h)...")
model_dir = snapshot_download(repo_id="danhtran2mind/Vi-F5-TTS", local_dir="Vi-F5-TTS")
print(f"-> Da tai xong vao thu muc: {model_dir}")

# Tim file checkpoint (.pt hoac .safetensors) va vocab.txt
ckpt_file = os.path.join(model_dir, "model_last.pt")
if not os.path.exists(ckpt_file):
    for f in os.listdir(model_dir):
        if f.endswith(".pt") or f.endswith(".safetensors"):
            ckpt_file = os.path.join(model_dir, f)
            break

vocab_file = os.path.join(model_dir, "vocab.txt")
print(f"-> Checkpoint : {ckpt_file}")
print(f"-> Vocab Tieng Viet: {vocab_file}")

# 2. Nap Vocoder va Model Tieng Viet
vocoder = load_vocoder(vocoder_name="vocos", is_local=False)
model_vi = load_model(
    model_cls=DiT,
    model_cfg=dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
    ckpt_path=ckpt_file,
    vocab_file=vocab_file,
    mel_spec_type="vocos",
    device=device
)
print("-> DA NAP THANH CONG MODEL TIENG VIET VI-F5-TTS!\n")

REF_WAV = "loc-dinh-ky.wav"
REF_TRANSCRIPT = "Những lời lẽ đê tiện như vậy mà ngươi cũng nói ra được hay sao hả?"

BENCHMARK_20 = [
    # Nhom 1: Dinh danh & Gioi thieu
    "Xin chào bạn, tôi là trợ lý giọng nói tiếng Việt cá nhân của bạn.",
    "Hôm nay là ngày 24 tháng 8 năm 2026, thời tiết tại Hà Nội rất trong lành.",
    "Tôi tên là Nguyễn Huy Hoàng, rất vui được đồng hành cùng bạn trong dự án này.",
    "Mỗi buổi sáng, việc đọc sách và rèn luyện thể thao giúp tinh thần luôn sảng khoái.",
    
    # Nhom 2: Tu phuc hop & Nguyen am co dau
    "Nguyễn Hoài Nam vừa hoàn thành thủ tục xuất nhập khẩu hàng hóa tại cảng Hải Phòng.",
    "Con đường quanh co uốn khúc ngoằn ngoèo đưa chúng tôi đến một thung lũng rực rỡ.",
    "Dưới ánh nắng ban mai, những giọt sương mai đọng trên cành lá lung linh kỳ ảo.",
    "Nghệ thuật điêu khắc gỗ truyền thống đòi hỏi sự tỉ mỉ, kiên nhẫn và đôi bàn tay khéo léo.",
    
    # Nhom 3: Thanh hoi & Thanh nga doi chieu
    "Bạn hãy giữ vững ý chí, vượt qua mọi nỗi gian truân và khó khăn thử thách.",
    "Kỷ niệm xưa cũ bỗng ùa về trong một buổi chiều thu yên ả và lộng gió.",
    "Sự hiểu biết sâu rộng cùng lòng kiên nhẫn sẽ mở ra những cánh cửa mới.",
    "Những bãi cỏ xanh mướt trải dài vô tận dưới chân dãy núi hùng vĩ.",
    
    # Nhom 4: So lieu, Ngay thang & Han Viet
    "Dự án đạt tăng trưởng 15.5% trong quý 3 năm 2026 với tổng doanh thu 120 tỷ đồng.",
    "Các chuyên gia công nghệ AI tại TP. Hồ Chí Minh vừa công bố báo cáo mới.",
    "Nhiệt độ trung bình tại khu vực miền Trung dao động từ 28 đến 34 độ C.",
    "Quy trình kiểm định chất lượng được thực hiện nghiêm ngặt qua 3 giai đoạn độc lập.",
    
    # Nhom 5: Hoi thoai, Bieu cam & Ngat nhip
    "Tuyệt vời quá! Chúng ta đã hoàn thành xuất sắc mục tiêu đề ra rồi!",
    "Bạn có tin rằng công nghệ giọng nói AI có thể học được cảm xúc của con người không?",
    "Hãy lắng nghe thật kỹ từng nhịp thở của tự nhiên, bạn sẽ cảm nhận được sự bình yên.",
    "Chặng đường phía trước còn nhiều điều thú vị đang chờ đón chúng ta cùng khám phá."
]

output_dir = "phase_a_vietnamese_results"
os.makedirs(output_dir, exist_ok=True)

print("=" * 65)
print("   BAT DAU TONG HOP 20 CAU BENCHMARK TIENG VIET CHUAN DAC")
print("=" * 65)

for i, sentence in enumerate(BENCHMARK_20, 1):
    out_wav = os.path.join(output_dir, f"cau_{i:02d}.wav")
    print(f"\n[{i:02d}/20] {sentence}")
    wav, sr, _ = infer_process(
        ref_audio=REF_WAV,
        ref_text=REF_TRANSCRIPT,
        gen_text=sentence,
        model_obj=model_vi,
        vocoder=vocoder,
        speed=0.95, # Toc do tu nhien chuan muc
        device=device
    )
    sf.write(out_wav, wav, sr)
    display(Audio(out_wav))

import shutil
shutil.make_archive("phase_a_vietnamese_results", 'zip', output_dir)
print("\n" + "=" * 65)
print("🎉 DA TONG HOP XONG 20 CAU TIENG VIET CHUAN DAC!")
print("-> File zip da luu tai: phase_a_vietnamese_results.zip")
print("=" * 65)
