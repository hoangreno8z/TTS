"""PHASE A: PROOF OF VOICE — 20 BENCHMARK EVALUATION SENTENCES.
Evaluates Vietnamese Zero-Shot Voice Cloning quality, naturalness, and diacritics accuracy.
"""
import os
import sys
import time

BENCHMARK_20_SENTENCES = [
    # Nhóm 1: Giới thiệu & Định danh (Identity & Basic Tone)
    "Xin chào bạn, tôi là trợ lý giọng nói tiếng Việt cá nhân của bạn.",
    "Hôm nay là ngày 24 tháng 8 năm 2026, thời tiết tại Hà Nội rất trong lành.",
    "Tôi tên là Nguyễn Huy Hoàng, rất vui được đồng hành cùng bạn trong dự án này.",
    "Mỗi buổi sáng, việc đọc sách và rèn luyện thể thao giúp tinh thần luôn sảng khoái.",
    
    # Nhóm 2: Thử thách nguyên âm có dấu & phụ âm ghép (Complex Vowels & Clusters)
    "Nguyễn Hoài Nam vừa hoàn thành thủ tục xuất nhập khẩu hàng hóa tại cảng Hải Phòng.",
    "Con đường quanh co uốn khúc ngoằn ngoèo đưa chúng tôi đến một thung lũng rực rỡ.",
    "Dưới ánh nắng ban mai, những giọt sương mai đọng trên cành lá lung linh kỳ ảo.",
    "Nghệ thuật điêu khắc gỗ truyền thống đòi hỏi sự tỉ mỉ, kiên nhẫn và đôi bàn tay khéo léo.",
    
    # Nhóm 3: Thanh hỏi & thanh ngã đối chiếu (Tones Contrast: Hỏi vs Ngã)
    "Bạn hãy giữ vững ý chí, vượt qua mọi nỗi gian truân và khó khăn thử thách.",
    "Kỷ niệm xưa cũ bỗng ùa về trong một buổi chiều thu yên ả và lộng gió.",
    "Sự hiểu biết sâu rộng cùng lòng kiên nhẫn sẽ mở ra những cánh cửa mới.",
    "Những bãi cỏ xanh mướt trải dài vô tận dưới chân dãy núi hùng vĩ.",
    
    # Nhóm 4: Số liệu, Ngày tháng, Viết tắt & Từ Hán Việt (Numbers & Proper Nouns)
    "Dự án đạt tăng trưởng 15.5% trong quý 3 năm 2026 với tổng doanh thu 120 tỷ đồng.",
    "Các chuyên gia công nghệ AI tại TP. Hồ Chí Minh vừa công bố báo cáo mới.",
    "Nhiệt độ trung bình tại khu vực miền Trung dao động từ 28 đến 34 độ C.",
    "Quy trình kiểm định chất lượng được thực hiện nghiêm ngặt qua 3 giai đoạn độc lập.",
    
    # Nhóm 5: Câu cảm thán, hội thoại & ngắt nhịp biểu cảm (Prosody & Expressive Dialog)
    "Tuyệt vời quá! Chúng ta đã hoàn thành xuất sắc mục tiêu đề ra rồi!",
    "Bạn có tin rằng công nghệ giọng nói AI có thể học được cảm xúc của con người không?",
    "Hãy lắng nghe thật kỹ từng nhịp thở của tự nhiên, bạn sẽ cảm nhận được sự bình yên.",
    "Chặng đường phía trước còn nhiều điều thú vị đang chờ đón chúng ta cùng khám phá."
]

def run_phase_a_benchmark(ref_audio_path: str, ref_transcript: str, engine_fn, output_dir: str = "benchmark/voice/outputs"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 65)
    print("   PHASE A: PROOF OF VOICE BENCHMARK (20 SENTENCES)")
    print("=" * 65)
    print(f"Reference Audio     : {ref_audio_path}")
    print(f"Reference Transcript: {ref_transcript}")
    print(f"Output Directory    : {output_dir}")
    print("-" * 65)

    results = []
    for idx, sentence in enumerate(BENCHMARK_20_SENTENCES, start=1):
        t0 = time.time()
        out_wav = os.path.join(output_dir, f"sent_{idx:02d}.wav")
        print(f"[{idx:02d}/20] Dang tong hop: \"{sentence[:45]}...\"")
        
        try:
            engine_fn(
                text=sentence,
                ref_audio=ref_audio_path,
                ref_transcript=ref_transcript,
                out_path=out_wav
            )
            elapsed = round(time.time() - t0, 2)
            results.append({"id": idx, "text": sentence, "status": "SUCCESS", "elapsed": elapsed, "file": out_wav})
            print(f"       -> [OK] Xong trong {elapsed}s ({out_wav})")
        except Exception as e:
            results.append({"id": idx, "text": sentence, "status": "FAILED", "error": str(e)})
            print(f"       -> [LOI] {e}")

    print("=" * 65)
    print(f"HOAN THANH PHASE A: {sum(1 for r in results if r['status'] == 'SUCCESS')}/20 cau thanh cong.")
    print("=" * 65)
    return results

if __name__ == "__main__":
    print("Benchmark Script Phase A loaded.")
