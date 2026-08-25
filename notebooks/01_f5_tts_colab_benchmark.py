"""Google Colab Reproducible Benchmark Script for F5-TTS (Vietnamese).
Run this on Google Colab with T4 GPU (Free Tier) to synthesize the 20 benchmark sentences.

Steps on Colab:
1. Set Runtime -> Change runtime type -> T4 GPU (Free)
2. Run this script!
"""

# Cell 1: Environment & Dependency Setup
# !pip install torch torchaudio soundfile librosa git+https://github.com/SWivid/F5-TTS.git cached_path

import os
import sys
import time
import json
import torch
import soundfile as sf

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")

# Cell 2: Benchmark 20 sentences definition
BENCHMARK_SENTENCES = [
    {"id": 1, "category": "câu ngắn", "text": "Xin chào, tôi là trợ lý giọng nói tiếng Việt cá nhân của bạn."},
    {"id": 2, "category": "câu ngắn", "text": "Hôm nay thời tiết thật là đẹp và trong lành."},
    {"id": 3, "category": "câu hỏi", "text": "Bạn có thể cho tôi biết dự báo thời tiết ngày mai ở Hà Nội thế nào không?"},
    {"id": 4, "category": "câu hỏi", "text": "Liệu công nghệ tổng hợp giọng nói có thể thay thế hoàn toàn con người?"},
    {"id": 5, "category": "câu cảm thán", "text": "Ôi, khung cảnh hoàng hôn trên bờ biển Phú Quốc tuyệt vời quá!"},
    {"id": 6, "category": "câu cảm thán", "text": "Thật không thể tin được là hệ thống xử lý nhanh đến như vậy!"},
    {"id": 7, "category": "số", "text": "Năm hai nghìn không trăm hai mươi sáu, dân số khu vực đạt khoảng một triệu hai trăm năm mươi nghìn người với ba trăm năm mươi hộ gia đình."},
    {"id": 8, "category": "số & tiền tệ", "text": "Mỗi chiếc vé xem phim có giá một trăm hai mươi nghìn đồng, tổng cộng hết sáu trăm nghìn đồng cho năm người."},
    {"id": 9, "category": "ngày tháng & thời gian", "text": "Vào ngày hai mươi tư tháng tám năm hai nghìn không trăm hai mươi sáu, hội nghị khoa học quốc tế sẽ chính thức khai mạc lúc tám giờ sáng."},
    {"id": 10, "category": "tỷ lệ phần trăm", "text": "Doanh thu quý này tăng trưởng mười tám phẩy năm phần trăm, vượt năm phần trăm so với chỉ tiêu ban đầu đề ra."},
    {"id": 11, "category": "tên riêng Việt Nam", "text": "Giáo sư Nguyễn Du, tác giả Truyện Kiều, là danh nhân văn hóa lỗi lạc của dân tộc."},
    {"id": 12, "category": "tên riêng & địa danh", "text": "Đoàn công tác đã đi qua Đà Nẵng, Nha Trang, Thành phố Hồ Chí Minh và dừng chân tại Cần Thơ."},
    {"id": 13, "category": "thanh điệu hỏi / ngã", "text": "Chúng ta cần bảo đảm tính chuẩn xác trong việc giữ gìn sự trong sáng của chữ nghĩa tiếng Việt."},
    {"id": 14, "category": "thanh điệu hỏi / ngã", "text": "Những suy nghĩ vĩ đại luôn khởi nguồn từ những trăn trở, nỗ lực và sự kiên trì không ngừng nghỉ."},
    {"id": 15, "category": "viết tắt & chức danh", "text": "Phó giáo sư Tiến sĩ Lê Văn C cùng Bác sĩ Trần Thị D đã công bố kết quả nghiên cứu y khoa mới."},
    {"id": 16, "category": "câu nhiều dấu phẩy & ngắt nhịp", "text": "Sách là kho tàng tri thức, là người bạn tâm giao, soi sáng con đường học vấn, bồi dưỡng tâm hồn và mở rộng tầm nhìn cho mỗi chúng ta."},
    {"id": 17, "category": "câu phức đối thoại", "text": "Anh ấy quay sang nhìn tôi, mỉm cười rồi khẽ nói, Hãy vững tin vào con đường mà bạn đã chọn lựa."},
    {"id": 18, "category": "câu dài ngữ điệu", "text": "Trải qua hàng ngàn năm lịch sử dựng nước và giữ nước, tinh thần đoàn kết, ý chí tự lực tự cường và lòng yêu nước nồng nàn luôn là nguồn sức mạnh to lớn đưa dân tộc Việt Nam vượt qua mọi thử thách."},
    {"id": 19, "category": "từ mượn quốc tế", "text": "Công nghệ AI, thuật toán Deep Learning và kiến trúc Transformer đang định hình lại tương lai của ngành xử lý ngôn ngữ tự nhiên."},
    {"id": 20, "category": "đoạn văn 500 ký tự", "text": "Mùa thu Hà Nội luôn mang một vẻ đẹp dịu dàng và trầm mặc rất riêng. Khi những cơn gió heo may đầu mùa thổi qua từng góc phố cổ, mùi hoa sữa thoang thoảng quyện trong không gian se lạnh khiến lòng người bâng khuâng khó tả. Những hàng cây cơm nguội vàng, cây bàng lá đỏ soi bóng xuống mặt nước Hồ Gươm phẳng lặng, tạo nên bức tranh thiên nhiên tuyệt mỹ mà bất cứ ai từng ghé thăm thủ đô cũng không thể nào quên được."}
]

# Cell 3: Load Model & Run Synthesis
def run_synthesis(ref_audio_path="ref_sample.wav", ref_text=""):
    os.makedirs("output_f5_tts", exist_ok=True)
    from f5_tts.infer.utils_infer import load_model, load_vocoder, infer_process
    from f5_tts.model import CFM, DiT

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading F5-TTS model on {device}...")
    vocoder = load_vocoder(vocoder_name="vocos", is_local=False)
    
    # Load default F5-TTS or Vietnamese model
    model_cls = DiT
    model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    model = load_model(model_cls, model_cfg, ckpt_path="F5TTS_Base/model_1200000.safetensors")

    print("\n--- Starting 20 Benchmark Sentences ---")
    for s in BENCHMARK_SENTENCES:
        s_id = s["id"]
        text = s["text"]
        out_file = f"output_f5_tts/f5_bench_{s_id:02d}.wav"
        t0 = time.time()
        wav, sr, _ = infer_process(
            ref_audio=ref_audio_path,
            ref_text=ref_text,
            gen_text=text,
            model_obj=model,
            vocoder=vocoder,
            device=device
        )
        sf.write(out_file, wav, sr)
        latency = round(time.time() - t0, 2)
        print(f"[{s_id:02d}/20] Generated in {latency}s -> {out_file}")

    print("\nBenchmark generation completed! Run '!zip -r f5_tts_benchmark.zip output_f5_tts' to download.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_synthesis(sys.argv[1])
    else:
        print("Ready. Pass ref_audio_path to run synthesis.")
