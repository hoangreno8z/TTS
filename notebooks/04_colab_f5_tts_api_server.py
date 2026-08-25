"""Google Colab F5-TTS Zero-Shot Voice Cloning API Server (Free T4 GPU).
Run this on Google Colab to enable 100% voice cloning for your LAPQUE TTS Web Studio!
"""

# Cell 1: Install Dependencies
# !pip install --quiet torch torchaudio soundfile librosa git+https://github.com/SWivid/F5-TTS.git fastapi uvicorn python-multipart pyngrok nest_asyncio

import os
import sys
import torch
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import nest_asyncio

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Device    : {torch.cuda.get_device_name(0)}")

# Load F5-TTS Model on Colab GPU
from f5_tts.infer.utils_infer import load_model, load_vocoder, infer_process

device = "cuda" if torch.cuda.is_available() else "cpu"
vocoder = load_vocoder(vocoder_name="vocos", is_local=False)
model_f5 = load_model(
    model_cls="DiT",
    model_cfg=dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
    ckpt_path="hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors",
    mel_spec_type="vocos",
    vocab_file="",
    device=device
)

app = FastAPI(title="LAPQUE Colab F5-TTS GPU Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "online", "device": device, "engine": "f5-tts-dit", "vram_free": "15GB T4"}

@app.post("/clone")
async def clone_voice(
    text: str = Form(...),
    ref_text: str = Form(default=""),
    speed: float = Form(default=1.0),
    file: UploadFile = File(...)
):
    os.makedirs("temp_colab", exist_ok=True)
    ref_path = os.path.join("temp_colab", file.filename or "ref.wav")
    with open(ref_path, "wb") as f:
        f.write(await file.read())

    out_path = os.path.join("temp_colab", "cloned_output.wav")
    wav, sr, _ = infer_process(
        ref_audio=ref_path,
        ref_text=ref_text,
        gen_text=text,
        model_obj=model_f5,
        vocoder=vocoder,
        speed=speed,
        device=device
    )
    sf.write(out_path, wav, sr)
    return FileResponse(out_path, media_type="audio/wav")

# Cell 2: Launch with Public Cloudflare / ngrok Tunnel
# !wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
# !chmod +x cloudflared-linux-amd64
# !./cloudflared-linux-amd64 tunnel --url http://127.0.0.1:8000 &
# uvicorn.run(app, host="127.0.0.1", port=8000)
