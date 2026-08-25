# -*- coding: utf-8 -*-
"""
LAPQUE RVC v2 — LIVE INFERENCE API SERVER (COLAB GPU -> LOCAL STUDIO)
Nhận âm thanh từ Edge TTS tiếng Việt -> Chuyển đổi qua model Lộc Đỉnh Ký RVC v2 đã train -> Trả về Web Studio.
"""

# ==============================================================================
# KHỞI CHẠY FASTAPI + CLOUDFLARE TUNNEL TRÊN GOOGLE COLAB
# ==============================================================================
"""
import os
import sys
import torch
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import uvicorn
from pycloudflared import try_cloudflare

app = FastAPI(title="LAPQUE RVC Inference Server")

# Load model weights
MODEL_NAME = "loc_dinh_ky.pth"
INDEX_PATH = "/content/RVC/logs/loc_dinh_ky/added_IVF256_Flat_Fast_loc_dinh_ky_v2.index"

# Khởi tạo RVC Pipeline
from infer.modules.vc.modules import VC
from configs.config import Config

config = Config()
config.device = "cuda:0"
config.is_half = True
vc = VC(config)
vc.get_vc(MODEL_NAME)

@app.post("/convert")
async def convert_voice(
    file: UploadFile = File(...),
    pitch_shift: int = Form(default=0),
    index_rate: float = Form(default=0.75)
):
    try:
        content = await file.read()
        in_path = "/content/temp_in.wav"
        out_path = "/content/temp_out.wav"
        with open(in_path, "wb") as f:
            f.write(content)

        # Chạy suy luận Neural Voice Conversion
        info, opt = vc.vc_single(
            sid=0,
            input_audio_path=in_path,
            f0_up_key=pitch_shift,
            f0_file=None,
            f0_method="rmvpe",
            file_index=INDEX_PATH if os.path.exists(INDEX_PATH) else "",
            file_index2="",
            index_rate=index_rate,
            filter_radius=3,
            resample_sr=0,
            rms_mix_rate=0.25,
            protect=0.33
        )
        
        if opt is not None:
            sr, wav_data = opt
            sf.write(out_path, wav_data, sr)
            with open(out_path, "rb") as f_res:
                return Response(content=f_res.read(), media_type="audio/wav")
        else:
            raise RuntimeError(f"RVC conversion error: {info}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chạy Server và tạo Public Cloudflare Tunnel
import threading
def run_app():
    uvicorn.run(app, host="0.0.0.0", port=8000)

t = threading.Thread(target=run_app)
t.start()

tunnel = try_cloudflare(port=8000)
print("="*60)
print(f"URL KẾT NỐI VÀO LAPQUE STUDIO:")
print(f" -> {tunnel.tunnel_url}")
print("="*60)
print("Dán URL này vào ô 'Kết nối Google Colab GPU' trong Web Studio!")
"""
