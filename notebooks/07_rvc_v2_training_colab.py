# -*- coding: utf-8 -*-
"""
LAPQUE RVC v2 — 1-CLICK COLAB TRAINING & VOICE CLONING (VIETNAMESE)
Huấn luyện mô hình nhân bản giọng nói thực sự (Neural Voice Conversion) từ 300 mẫu audio Lộc Đỉnh Ký.
Chạy trên Google Colab Free (T4 GPU - 15GB VRAM) hoàn toàn miễn phí.
"""

# ==============================================================================
# BƯỚC 1: CÀI ĐẶT MÔI TRƯỜNG RVC V2 & TẢI PRETRAINED BASE WEIGHTS
# ==============================================================================
"""
!git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git /content/RVC
%cd /content/RVC

# Cài đặt thư viện phụ thuộc
!pip install -r requirements.txt
!pip install pycloudflared soundfile

# Tải Pretrained HuBERT & RMVPE Pitch Estimator
!mkdir -p assets/hubert assets/rmvpe assets/pretrained_v2
!wget -O assets/hubert/hubert_base.pt https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
!wget -O assets/rmvpe/rmvpe.pt https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt
!wget -O assets/pretrained_v2/f0G40k.pth https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0G40k.pth
!wget -O assets/pretrained_v2/f0D40k.pth https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0D40k.pth
print("-> Đã nạp thành công Pretrained Neural Base Weights!")
"""

# ==============================================================================
# BƯỚC 2: TẢI DATASET 300 AUDIO CLIPS (LỘC ĐỈNH KÝ 40KHZ)
# ==============================================================================
"""
import os
import zipfile

dataset_dir = "/content/RVC/dataset_loc_dinh_ky"
os.makedirs(dataset_dir, exist_ok=True)

# Bạn có thể upload file 'data/dataset_loc_dinh_ky_40k.zip' trực tiếp vào Colab Files:
if os.path.exists("/content/dataset_loc_dinh_ky_40k.zip"):
    with zipfile.ZipFile("/content/dataset_loc_dinh_ky_40k.zip", 'r') as zip_ref:
        zip_ref.extractall(dataset_dir)
    print(f"-> Đã giải nén thành công {len(os.listdir(dataset_dir))} file âm thanh huấn luyện!")
else:
    print("Vui lòng kéo thả file 'dataset_loc_dinh_ky_40k.zip' vào tab Files bên trái Colab!")
"""

# ==============================================================================
# BƯỚC 3: TRÍCH XUẤT ĐẶC TRƯNG HUBERT & PITCH RMVPE (FEATURE EXTRACTION)
# ==============================================================================
"""
# 1. Tiền xử lý audio 40kHz
!python infer/modules/train/preprocess.py /content/RVC/dataset_loc_dinh_ky 40000 2 /content/RVC/logs/loc_dinh_ky False 3.0

# 2. Trích xuất cao độ F0 (RMVPE) & HuBERT Semantic Features
!python infer/modules/train/extract/extract_f0_rmvpe.py 2 0 0 /content/RVC/logs/loc_dinh_ky True
!python infer/modules/train/extract_feature_print.py cuda:0 1 0 0 /content/RVC/logs/loc_dinh_ky v2
print("-> Hoàn tất trích xuất đặc trưng giọng nói!")
"""

# ==============================================================================
# BƯỚC 4: HUẤN LUYỆN MÔ HÌNH THỰC SỰ (TRAIN GENERATOR + DISCRIMINATOR)
# ==============================================================================
"""
# Huấn luyện 150 Epochs (~15-20 phút trên GPU T4)
!python infer/modules/train/train.py -e loc_dinh_ky -sr 40k -f0 1 -bs 8 -g 0 -te 150 -se 25 -pg assets/pretrained_v2/f0G40k.pth -pd assets/pretrained_v2/f0D40k.pth -l 1 -c 0 -sw 1 -v v2

# Xây dựng Faiss Index cho âm sắc mục tiêu
!python infer/modules/train/train_index.py /content/RVC/logs/loc_dinh_ky v2
print("-> HUẤN LUYỆN HOÀN TẤT 100%! ĐÃ TẠO WEIGHTS .PTH VÀ INDEX .INDEX")
"""

# ==============================================================================
# BƯỚC 5: XUẤT FILE MODEL VÀ KHỞI ĐỘNG LIVE API SERVER CLOUD TUNNEL
# ==============================================================================
"""
# Tải model về máy:
from google.colab import files
import glob

pth_files = glob.glob("/content/RVC/assets/weights/loc_dinh_ky*.pth")
index_files = glob.glob("/content/RVC/logs/loc_dinh_ky/*.index")

print("Files sẵn sàng tải về máy để đưa vào LAPQUE Studio local:")
for f in pth_files + index_files:
    print(f" -> {f}")
"""
