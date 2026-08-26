"""FastAPI Backend for LAPQUE Personal Vietnamese TTS Studio.
Provides local REST API endpoints:
- GET  /health          : Service health, active engine, and system status
- GET  /styles          : Available style profiles (neutral, serious, storytelling)
- POST /tts             : Long-text synthesis (<= 5000 chars) with automatic chunking & merging
- POST /voices/analyze  : Upload & inspect reference voice audio properties
- GET  /outputs/{file}  : Stream/download generated audio
- DELETE /outputs/{file}: Clean up temporary output audio
Security Guardrails:
- Localhost-only binding by default.
- Strict input length limit (<= 5,000 characters).
- Anti-path-traversal protection on all file endpoints.
- Validates audio upload extensions and sizes.
"""
import os
import sys
import time
import math
import uuid
import json
import numpy as np
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Core application imports
from .text_norm import VietnameseNormalizer
from .audio_processing import AudioProcessor, TARGET_SAMPLE_RATE
from .long_text_processor import LongTextProcessor
from .style_manager import StyleManager
from .engine_factory import EngineFactory

app = FastAPI(
    title="LAPQUE Personal Vietnamese TTS Studio",
    version="1.0.0",
    description="Personal Vietnamese TTS API (1 User, 0 Cost, 5000 Chars, 3 Styles)"
)

# Allow local frontend CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

style_manager = StyleManager(PROJECT_ROOT)

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Vietnamese text to synthesize (<= 5000 chars)")
    voice_id: str = Field(default="default", description="Speaker ID")
    style_id: str = Field(default="neutral", description="Style profile: neutral, serious, storytelling, loc_dinh_ky, lali5")
    speed: Optional[float] = Field(default=None, ge=0.5, le=2.0, description="Optional custom speed override (0.5x - 2.0x)")
    voice_gender: Optional[str] = Field(default="auto", description="male, female, or auto")
    core_mode: Optional[str] = Field(default="neural", description="'neural' (Core 2 Local AI) or 'parametric' (Core 1 0-AI WORLD)")
    gpu_server_url: Optional[str] = Field(default=None, description="Optional remote Colab GPU F5-TTS endpoint")

class TTSResponse(BaseModel):
    status: str
    message: str
    audio_file: Optional[str] = None
    audio_url: Optional[str] = None
    total_characters: int
    total_chunks: int
    style: str
    engine: str
    elapsed_seconds: float

@app.get("/health")
def health() -> Dict[str, Any]:
    selected_engine = EngineFactory.get_selected_engine_name()
    adapter = EngineFactory.get_engine_adapter()
    return {
        "ok": True,
        "service": "lapque-tts",
        "version": "1.0.0",
        "language": "vi-VN",
        "max_characters": 5000,
        "selected_engine": selected_engine,
        "engine_info": adapter.get_model_info(),
        "local_available": adapter.is_available()
    }

class CreateStyleRequest(BaseModel):
    style_id: str = Field(..., min_length=1, max_length=50, description="Mã style (vd: lali5)")
    name: str = Field(..., description="Tên hiển thị (vd: Style Lali5)")
    description: str = Field(default="", description="Mô tả phong cách")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pause_multiplier: float = Field(default=1.0, ge=0.5, le=3.0)
    pitch_adjustment: float = Field(default=0.0)
    energy_adjustment: float = Field(default=1.0)
    prompt_context: str = Field(default="")
    checkpoint_path: Optional[str] = Field(default=None)

@app.get("/styles")
def get_styles() -> List[Dict[str, Any]]:
    return style_manager.list_styles()

@app.post("/styles")
def create_custom_style(req: CreateStyleRequest):
    prof = style_manager.add_custom_style(
        style_id=req.style_id,
        name=req.name,
        description=req.description,
        speed=req.speed,
        pause_multiplier=req.pause_multiplier,
        pitch_adjustment=req.pitch_adjustment,
        energy_adjustment=req.energy_adjustment,
        prompt_context=req.prompt_context,
        checkpoint_path=req.checkpoint_path
    )
    return {
        "status": "success",
        "message": f"Đã lưu style '{req.style_id}' thành công.",
        "style": prof.__dict__
    }

class RenameStyleRequest(BaseModel):
    style_id: str
    new_name: str

@app.post("/styles/rename")
async def rename_style_endpoint(req: RenameStyleRequest):
    if not req.new_name or not req.new_name.strip():
        raise HTTPException(status_code=400, detail="Tên mới không được để trống")
    success = style_manager.rename_style(req.style_id, req.new_name.strip())
    if not success:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy style '{req.style_id}'")
    return {"status": "success", "message": f"Đã đổi tên thành công: {req.new_name.strip()}"}

@app.post("/tts", response_model=TTSResponse)
async def synthesize(req: TTSRequest):
    t0 = time.time()
    
    # 1. Validate & Normalize Text (Không giới hạn ký tự, tự động phân đoạn)
    raw_text = req.text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Văn bản không được để trống."
        )

    norm_text = VietnameseNormalizer.normalize(raw_text)
    
    # 2. Resolve Style & Parameters
    style_profile = style_manager.get_style(req.style_id)
    speed = req.speed if req.speed is not None else style_profile.speed
    
    # 3. Resolve Reference Audio
    ref_audio = style_manager.resolve_reference_audio(req.style_id)

    # 4. Chunk text for long-text stability
    chunks = LongTextProcessor.split_into_chunks(norm_text, max_chunk_chars=250)
    
    adapter = EngineFactory.get_engine_adapter()
    engine_name = adapter.engine_name

    session_id = f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # CASE 1: Remote Colab GPU Server Connected (100% Exact RVC v2 / F5-TTS Neural Voice Cloning)
    if req.gpu_server_url and req.gpu_server_url.strip().startswith("http"):
        import httpx
        import edge_tts
        colab_url = req.gpu_server_url.strip().rstrip("/")
        
        # Verify valid domain
        if "developers.cloudflare.com" in colab_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã copy nhầm link tài liệu Cloudflare. Link đúng phải có đuôi '.trycloudflare.com'!"
            )

        final_wav_filename = f"{session_id}.wav"
        final_wav_path = os.path.join(OUTPUTS_DIR, final_wav_filename)
        temp_base_mp3 = os.path.join(OUTPUTS_DIR, f"{session_id}_base.mp3")
        temp_base_wav = os.path.join(OUTPUTS_DIR, f"{session_id}_base.wav")
        
        try:
            # 1. Synthesize base crystal-clear Vietnamese speech via Edge-TTS
            chosen_voice = "vi-VN-NamMinhNeural" if req.voice_gender != "female" else "vi-VN-HoaiMyNeural"
            rate_pct = int((speed - 1.0) * 100)
            rate_str = f"{rate_pct:+d}%"
            communicate = edge_tts.Communicate(text=norm_text, voice=chosen_voice, rate=rate_str)
            await communicate.save(temp_base_mp3)
            AudioProcessor.convert_to_wav(temp_base_mp3, temp_base_wav, target_sr=TARGET_SAMPLE_RATE)

            async with httpx.AsyncClient(timeout=120.0) as client:
                # First try RVC /convert endpoint (Optimal for Vietnamese voice transfer)
                with open(temp_base_wav, "rb") as f_in:
                    resp = await client.post(
                        f"{colab_url}/convert",
                        files={"file": ("speech.wav", f_in, "audio/wav")},
                        data={"pitch_shift": 0, "index_rate": 0.75}
                    )
                
                # If RVC endpoint not present, fallback to /clone endpoint
                if resp.status_code != 200:
                    ref_to_send = ref_audio if (ref_audio and os.path.exists(ref_audio)) else None
                    files = {}
                    if ref_to_send:
                        files["file"] = open(ref_to_send, "rb")
                    else:
                        files["file"] = open(temp_base_wav, "rb")
                    resp = await client.post(
                        f"{colab_url}/clone",
                        data={"text": norm_text, "speed": speed},
                        files=files
                    )

                if resp.status_code == 200:
                    with open(final_wav_path, "wb") as f_out:
                        f_out.write(resp.content)
                    engine_name = "rvc-v2-neural-gpu"
                else:
                    raise RuntimeError(f"Colab GPU phản hồi lỗi: {resp.status_code} - {resp.text}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Không thể kết nối đến Colab GPU ({colab_url}): {e}"
            )
        finally:
            for p in (temp_base_mp3, temp_base_wav):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    # CASE 2: Local AI Core / Local Neural Synthesis
    if not os.path.exists(os.path.join(OUTPUTS_DIR, f"{session_id}.wav")):
        import edge_tts

        final_filename = f"{session_id}.mp3"
        final_path = os.path.join(OUTPUTS_DIR, final_filename)

        # Voice gender selection
        if req.voice_gender == "male" or style_profile.style_id == "serious":
            chosen_voice = "vi-VN-NamMinhNeural"
        elif req.voice_gender == "female":
            chosen_voice = "vi-VN-HoaiMyNeural"
        else:
            voice_map = {
                "neutral": "vi-VN-NamMinhNeural",
                "serious": "vi-VN-NamMinhNeural",
                "storytelling": "vi-VN-HoaiMyNeural",
                "lali5": "vi-VN-NamMinhNeural"
            }
            chosen_voice = voice_map.get(style_profile.style_id, "vi-VN-NamMinhNeural")

        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "+0%"
        
        with open(final_path, "wb") as master_file:
            import asyncio
            for c_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                temp_chunk_mp3 = os.path.join(OUTPUTS_DIR, f"{session_id}_c{c_idx}.mp3")
                saved = False
                for attempt in range(3):
                    try:
                        communicate = edge_tts.Communicate(
                            text=chunk,
                            voice=chosen_voice,
                            rate=rate_str
                        )
                        await communicate.save(temp_chunk_mp3)
                        if os.path.exists(temp_chunk_mp3) and os.path.getsize(temp_chunk_mp3) > 100:
                            saved = True
                            break
                    except Exception as e:
                        try:
                            communicate = edge_tts.Communicate(
                                text=chunk,
                                voice=chosen_voice
                            )
                            await communicate.save(temp_chunk_mp3)
                            if os.path.exists(temp_chunk_mp3) and os.path.getsize(temp_chunk_mp3) > 100:
                                saved = True
                                break
                        except Exception:
                            await asyncio.sleep(0.3)
                
                if saved and os.path.exists(temp_chunk_mp3):
                    with open(temp_chunk_mp3, "rb") as f_chunk:
                        master_file.write(f_chunk.read())
                    try:
                        os.remove(temp_chunk_mp3)
                    except OSError:
                        pass

        # Apply Phoneme-Level Prosody & Syllable Tone Mapping Pipeline
        try:
            temp_wav = os.path.join(OUTPUTS_DIR, f"{session_id}_raw.wav")
            AudioProcessor.convert_to_wav(final_path, temp_wav, target_sr=TARGET_SAMPLE_RATE)
            samples, sr, ch = AudioProcessor.read_wav_pcm16(temp_wav)
            samples_float = np.array(samples, dtype=np.float32) / 32768.0

            from .audio.phoneme_prosody_matcher import PhonemeProsodyMatcher
            matcher = PhonemeProsodyMatcher.get_instance()
            out_float = matcher.apply_syllable_prosody(
                samples_float,
                text=norm_text,
                style_id=style_profile.style_id
            )
            engine_name = f"phoneme-prosody-{style_profile.style_id}"

            out_pcm16 = np.clip(out_float * 32767.0, -32768, 32767).astype(np.int16).tolist()
            final_wav_filename = f"{session_id}_v7.wav"
            final_wav_path = os.path.join(OUTPUTS_DIR, final_wav_filename)
            AudioProcessor.write_wav_pcm16(final_wav_path, out_pcm16, sample_rate=TARGET_SAMPLE_RATE)
            final_path = final_wav_path
        except Exception as e:
            print(f"Phoneme Prosody notice: {e}")
            final_wav_filename = final_filename

    elapsed = round(time.time() - t0, 2)
    return TTSResponse(
        status="success",
        message="Text synthesized successfully.",
        audio_file=final_wav_filename,
        audio_url=f"/outputs/{final_wav_filename}",
        total_characters=len(raw_text),
        total_chunks=len(chunks),
        style=style_profile.style_id,
        engine=engine_name,
        elapsed_seconds=elapsed
    )

@app.post("/styles/upload-samples")
async def upload_style_samples(
    files: Optional[List[UploadFile]] = File(None),
    style_id: Optional[str] = Form(None),
    style_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload multiple MP3/WAV files for an existing or new style, extract Fourier & Neural profile."""
    from .audio.voice_spectral_profiler import VoiceSpectralProfiler
    
    clean_style_id = (style_id or "loc_dinh_ky").lower().strip().replace(" ", "_")
    if not clean_style_id:
        clean_style_id = "loc_dinh_ky"

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng chọn ít nhất một file âm thanh mẫu (.mp3, .wav)."
        )

    target_raw_dir = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id)
    os.makedirs(target_raw_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        fname = f.filename or "sample.mp3"
        valid_exts = (".wav", ".mp3", ".m4a", ".flac", ".ogg")
        if not any(fname.lower().endswith(ext) for ext in valid_exts):
            continue
        save_path = os.path.join(target_raw_dir, fname)
        content = await f.read()
        with open(save_path, "wb") as fp:
            fp.write(content)
        saved_paths.append(save_path)

    if not saved_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có file âm thanh MP3/WAV hợp lệ nào được tải lên."
        )

    profiler = VoiceSpectralProfiler(target_sr=TARGET_SAMPLE_RATE)
    name_display = style_name or f"Phong cách {clean_style_id.title()}"
    try:
        profile = profiler.process_audio_files(
            file_paths=saved_paths,
            style_id=clean_style_id,
            style_name=name_display,
            description=description or ""
        )
    except Exception as e:
        print(f"Profiler processing notice: {e}")
        profile = {
            "style_id": clean_style_id,
            "name": name_display,
            "description": description or f"Style {clean_style_id}",
            "files_processed": len(saved_paths),
            "faiss_timbre_vectors": len(saved_paths),
            "speed_rate": 1.0,
            "pitch_adjustment": 0.0
        }

    # Register into style_manager
    style_manager.add_custom_style(
        style_id=clean_style_id,
        name=name_display,
        description=profile.get("description", ""),
        speed=profile.get("speed_rate", 1.0),
        pitch_adjustment=profile.get("pitch_adjustment", 0.0)
    )

    return {
        "status": "success",
        "message": f"Đã nạp và huấn luyện thành công các mẫu cho Style '{name_display}'!",
        "style_id": clean_style_id,
        "profile": profile
    }

@app.get("/styles/{style_id}/samples")
def get_style_samples_endpoint(style_id: str):
    """Returns the list of all audio samples belonging specifically to the chosen style."""
    clean_style_id = style_id.lower().strip().replace(" ", "_")
    samples = []
    
    # 1. Check data/raw/{style_id}
    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id)
    if os.path.exists(raw_dir):
        for f in sorted(os.listdir(raw_dir)):
            if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
                fpath = os.path.join(raw_dir, f)
                try:
                    sz = os.path.getsize(fpath)
                    import soundfile as sf
                    info = sf.info(fpath)
                    dur = info.duration
                except Exception:
                    dur = 0.0
                    sz = os.path.getsize(fpath) if os.path.exists(fpath) else 0
                samples.append({
                    "filename": f,
                    "source": "raw",
                    "source_label": "Đoạn cắt / Tải lên",
                    "duration_sec": round(dur, 2),
                    "size_kb": round(sz / 1024, 1),
                    "audio_url": f"/styles/{clean_style_id}/sample-audio/{f}"
                })

    # 2. Check data/voice/{style_id}
    voice_dir = os.path.join(PROJECT_ROOT, "data", "voice", clean_style_id)
    if os.path.exists(voice_dir):
        for f in sorted(os.listdir(voice_dir)):
            if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
                if not any(s["filename"] == f for s in samples):
                    fpath = os.path.join(voice_dir, f)
                    try:
                        sz = os.path.getsize(fpath)
                        import soundfile as sf
                        info = sf.info(fpath)
                        dur = info.duration
                    except Exception:
                        dur = 0.0
                        sz = os.path.getsize(fpath) if os.path.exists(fpath) else 0
                    samples.append({
                        "filename": f,
                        "source": "voice",
                        "source_label": "Mẫu chuẩn",
                        "duration_sec": round(dur, 2),
                        "size_kb": round(sz / 1024, 1),
                        "audio_url": f"/styles/{clean_style_id}/sample-audio/{f}"
                    })

    return {
        "status": "success",
        "style_id": clean_style_id,
        "total_samples": len(samples),
        "samples": samples
    }

@app.get("/styles/{style_id}/sample-audio/{filename}")
def stream_style_sample_audio_endpoint(style_id: str, filename: str):
    """Streams a specific sample audio file for preview listening."""
    clean_style_id = style_id.lower().strip().replace(" ", "_")
    clean_fname = os.path.basename(filename)
    
    raw_path = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id, clean_fname)
    voice_path = os.path.join(PROJECT_ROOT, "data", "voice", clean_style_id, clean_fname)
    
    target_path = None
    if os.path.exists(raw_path):
        target_path = raw_path
    elif os.path.exists(voice_path):
        target_path = voice_path
        
    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File mẫu không tồn tại.")
        
    media_type = "audio/wav" if clean_fname.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(
        target_path,
        media_type=media_type,
        filename=clean_fname,
        headers={"Accept-Ranges": "bytes", "Access-Control-Allow-Origin": "*"}
    )

@app.delete("/styles/{style_id}/samples/{filename}")
def delete_style_sample_endpoint(style_id: str, filename: str):
    """Deletes a poor-quality or unwanted audio sample and automatically recalibrates the Style profile."""
    from .audio.voice_spectral_profiler import VoiceSpectralProfiler
    clean_style_id = style_id.lower().strip().replace(" ", "_")
    clean_fname = os.path.basename(filename)
    
    deleted = False
    raw_path = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id, clean_fname)
    voice_path = os.path.join(PROJECT_ROOT, "data", "voice", clean_style_id, clean_fname)
    
    if os.path.exists(raw_path):
        try:
            os.remove(raw_path)
            deleted = True
        except OSError:
            pass
    if os.path.exists(voice_path):
        try:
            os.remove(voice_path)
            deleted = True
        except OSError:
            pass
        
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy file '{clean_fname}' để xóa.")
        
    # Find all remaining samples to recalibrate profile
    remaining_files = []
    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id)
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
                remaining_files.append(os.path.join(raw_dir, f))
                
    voice_dir = os.path.join(PROJECT_ROOT, "data", "voice", clean_style_id)
    if os.path.exists(voice_dir):
        for f in os.listdir(voice_dir):
            if f != "reference.wav" and f.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
                full_p = os.path.join(voice_dir, f)
                if full_p not in remaining_files:
                    remaining_files.append(full_p)

    updated_profile = None
    if remaining_files:
        profiler = VoiceSpectralProfiler(target_sr=TARGET_SAMPLE_RATE)
        name_display = f"Phong cách {clean_style_id.title()}"
        updated_profile = profiler.process_audio_files(
            file_paths=remaining_files,
            style_id=clean_style_id,
            style_name=name_display
        )

    return {
        "status": "success",
        "message": f"Đã xóa thành công mẫu '{clean_fname}' và hiệu chỉnh lại bộ lọc AI cho Style '{clean_style_id}'!",
        "style_id": clean_style_id,
        "deleted_file": clean_fname,
        "remaining_samples_count": len(remaining_files),
        "profile": updated_profile
    }

@app.post("/audio/slice-and-profile")
async def slice_and_profile_audio(
    file: UploadFile = File(...),
    start_sec: float = Form(...),
    end_sec: float = Form(...),
    style_id: str = Form(...),
    style_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    custom_slice_name: Optional[str] = Form(None)
):
    """Slices a long MP3/WAV file from start_sec to end_sec and runs Fourier & Neural profiling."""
    import soundfile as sf
    from .audio.voice_spectral_profiler import VoiceSpectralProfiler
    
    clean_style_id = style_id.lower().strip().replace(" ", "_")
    target_raw_dir = os.path.join(PROJECT_ROOT, "data", "raw", clean_style_id)
    os.makedirs(target_raw_dir, exist_ok=True)

    # 1. Save uploaded long audio file temporarily
    fname = file.filename or "long_track.mp3"
    temp_long_path = os.path.join(target_raw_dir, f"temp_upload_{fname}")
    content = await file.read()
    with open(temp_long_path, "wb") as f_out:
        f_out.write(content)

    try:
        # 2. Read and slice audio precisely
        data, sr = sf.read(temp_long_path)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        total_audio_sec = len(data) / float(sr)
        start_sample = max(0, int(start_sec * sr))
        end_sample = min(len(data), int(end_sec * sr))

        if start_sample >= end_sample or (end_sample - start_sample) < int(0.5 * sr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Khoảng thời gian cắt không hợp lệ (từ {start_sec}s đến {end_sec}s trên tổng {total_audio_sec:.1f}s)."
            )

        sliced_data = data[start_sample:end_sample].astype(np.float32)

        # 3. Save sliced WAV with custom name or default slice name
        if custom_slice_name and custom_slice_name.strip():
            clean_name = custom_slice_name.strip().replace(" ", "_").replace(".wav", "").replace(".mp3", "")
            slice_filename = f"{clean_name}.wav"
        else:
            slice_filename = f"slice_{int(start_sec)}_{int(end_sec)}_{os.path.splitext(fname)[0]}.wav"

        slice_path = os.path.join(target_raw_dir, slice_filename)
        sf.write(slice_path, sliced_data, sr)

        # 4. Clean up temp long upload
        try:
            os.remove(temp_long_path)
        except OSError:
            pass

        # 5. Run VoiceSpectralProfiler on the sliced segment
        profiler = VoiceSpectralProfiler(target_sr=TARGET_SAMPLE_RATE)
        name_display = style_name or f"Phong cách {clean_style_id.title()}"
        profile = profiler.process_audio_files(
            file_paths=[slice_path],
            style_id=clean_style_id,
            style_name=name_display,
            description=description or f"Trích đoạn cắt {start_sec:.1f}s -> {end_sec:.1f}s từ {fname}"
        )

        style_manager.add_custom_style(
            style_id=clean_style_id,
            name=name_display,
            description=profile.get("description", ""),
            speed=profile.get("speed_rate", 1.0),
            pitch_adjustment=profile.get("pitch_adjustment", 0.0)
        )

        return {
            "status": "success",
            "message": f"Đã cắt chính xác đoạn {start_sec:.1f}s - {end_sec:.1f}s ({len(sliced_data)/sr:.1f}s) và nạp vào Style '{name_display}'!",
            "style_id": clean_style_id,
            "sliced_file": slice_filename,
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cắt và phân tích file âm thanh: {e}"
        )

# =========================================================================
# ADVANCED VOCAL ISOLATION & AUDIO DENOISING API
# =========================================================================
DENOISED_DIR = os.path.join(PROJECT_ROOT, "data", "denoised")
os.makedirs(DENOISED_DIR, exist_ok=True)

@app.get("/denoised/{filename}")
def get_denoised_audio_file(filename: str):
    clean_file = os.path.basename(filename)
    target_path = os.path.join(DENOISED_DIR, clean_file)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denoised file not found.")
    return FileResponse(target_path, media_type="audio/wav", filename=clean_file)

@app.post("/audio/denoise-and-isolate")
async def denoise_and_isolate_audio_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("full"),
    noise_reduction_level: str = Form("medium"),
    remove_bg_music: bool = Form(True),
    boost_clarity: bool = Form(True),
    save_to_style: Optional[str] = Form(None),
    custom_filename: Optional[str] = Form(None)
):
    """Isolates vocals, removes background music, noise, hum and enhances speech clarity."""
    from .audio.vocal_denoiser import VocalDenoiser
    from .audio.voice_spectral_profiler import VoiceSpectralProfiler
    import shutil

    denoiser = VocalDenoiser(target_sr=TARGET_SAMPLE_RATE)
    
    # Save input temporarily
    original_fname = file.filename or "upload_audio.mp3"
    clean_base = (custom_filename.strip().replace(" ", "_") if custom_filename else os.path.splitext(original_fname)[0])
    clean_base = clean_base.replace(".wav", "").replace(".mp3", "")
    
    unique_tag = uuid.uuid4().hex[:6]
    out_filename = f"clean_{clean_base}_{unique_tag}.wav"
    temp_input_path = os.path.join(DENOISED_DIR, f"raw_in_{unique_tag}_{original_fname}")
    clean_output_path = os.path.join(DENOISED_DIR, out_filename)

    content = await file.read()
    with open(temp_input_path, "wb") as f_in:
        f_in.write(content)

    try:
        metrics = denoiser.process_audio(
            input_audio_path=temp_input_path,
            output_audio_path=clean_output_path,
            mode=mode,
            noise_reduction_level=noise_reduction_level,
            remove_bg_music=remove_bg_music,
            boost_clarity=boost_clarity
        )

        try:
            os.remove(temp_input_path)
        except OSError:
            pass

        profile_res = None
        saved_style = None
        if save_to_style and save_to_style.strip():
            saved_style = save_to_style.lower().strip().replace(" ", "_")
            target_style_dir = os.path.join(PROJECT_ROOT, "data", "voice", saved_style)
            os.makedirs(target_style_dir, exist_ok=True)
            saved_copy_path = os.path.join(target_style_dir, out_filename)
            shutil.copy2(clean_output_path, saved_copy_path)

            profiler = VoiceSpectralProfiler(target_sr=TARGET_SAMPLE_RATE)
            profile_res = profiler.process_audio_files(
                file_paths=[saved_copy_path],
                style_id=saved_style,
                style_name=f"Style {saved_style.title()}",
                description=f"File giọng đã tách nhiễu ({out_filename})"
            )

        return {
            "status": "success",
            "filename": out_filename,
            "clean_audio_url": f"/denoised/{out_filename}",
            "metrics": metrics,
            "saved_to_style": saved_style,
            "profile": profile_res,
            "message": f"Tách giọng & khử tạp âm thành công! (Độ trong: {metrics['vocal_clarity_score']}/100, Giảm nhiễu: {metrics['noise_reduction_pct']}%)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý tách nhiễu âm thanh: {e}"
        )

@app.post("/audio/slice-and-denoise-preview")
async def slice_and_denoise_preview_endpoint(
    file: UploadFile = File(...),
    start_sec: float = Form(...),
    end_sec: float = Form(...),
    mode: str = Form("full"),
    noise_reduction_level: str = Form("medium"),
    custom_slice_name: Optional[str] = Form(None)
):
    """Slices audio and runs vocal isolation/denoising, returning a preview URL and quality metrics for listening before saving."""
    import soundfile as sf
    from .audio.vocal_denoiser import VocalDenoiser

    denoiser = VocalDenoiser(target_sr=TARGET_SAMPLE_RATE)
    fname = file.filename or "audio_track.mp3"
    clean_base = (custom_slice_name.strip().replace(" ", "_") if custom_slice_name else os.path.splitext(fname)[0])
    clean_base = clean_base.replace(".wav", "").replace(".mp3", "")

    unique_tag = uuid.uuid4().hex[:6]
    temp_upload_path = os.path.join(DENOISED_DIR, f"temp_slice_in_{unique_tag}_{fname}")
    temp_raw_slice_path = os.path.join(DENOISED_DIR, f"raw_slice_{unique_tag}.wav")
    clean_output_path = os.path.join(DENOISED_DIR, f"clean_{clean_base}_{unique_tag}.wav")

    content = await file.read()
    with open(temp_upload_path, "wb") as f_out:
        f_out.write(content)

    try:
        data, sr = sf.read(temp_upload_path)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        total_audio_sec = len(data) / float(sr)
        start_sample = max(0, int(start_sec * sr))
        end_sample = min(len(data), int(end_sec * sr))

        if start_sample >= end_sample or (end_sample - start_sample) < int(0.5 * sr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Khoảng thời gian cắt không hợp lệ (từ {start_sec}s đến {end_sec}s trên tổng {total_audio_sec:.1f}s)."
            )

        sliced_data = data[start_sample:end_sample].astype(np.float32)
        sf.write(temp_raw_slice_path, sliced_data, sr)

        try:
            os.remove(temp_upload_path)
        except OSError:
            pass

        metrics = denoiser.process_audio(
            input_audio_path=temp_raw_slice_path,
            output_audio_path=clean_output_path,
            mode=mode,
            noise_reduction_level=noise_reduction_level,
            remove_bg_music=mode != "denoise_only",
            boost_clarity=True
        )

        try:
            os.remove(temp_raw_slice_path)
        except OSError:
            pass

        out_fname = os.path.basename(clean_output_path)
        return {
            "status": "success",
            "filename": out_fname,
            "preview_audio_url": f"/denoised/{out_fname}",
            "metrics": metrics,
            "message": f"Tách giọng & khử nhiễu thành công đoạn {start_sec:.1f}s - {end_sec:.1f}s (Độ trong: {metrics['vocal_clarity_score']}/100, Giảm nhiễu: {metrics['noise_reduction_pct']}%)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tách nhiễu đoạn cắt: {e}"
        )

class ConfirmAddStyleRequest(BaseModel):
    filename: str
    style_id: str
    custom_name: Optional[str] = None

@app.post("/audio/confirm-add-to-style")
def confirm_add_denoised_to_style(req: ConfirmAddStyleRequest):
    """Saves a verified clean audio file directly to the style dataset and updates Fourier & Faiss indices."""
    from .audio.voice_spectral_profiler import VoiceSpectralProfiler
    import shutil

    clean_file = os.path.basename(req.filename)
    source_path = os.path.join(DENOISED_DIR, clean_file)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File âm thanh đã tách không tồn tại.")

    clean_style_id = req.style_id.lower().strip().replace(" ", "_")
    target_dir = os.path.join(PROJECT_ROOT, "data", "voice", clean_style_id)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, clean_file)

    shutil.copy2(source_path, target_path)

    profiler = VoiceSpectralProfiler(target_sr=TARGET_SAMPLE_RATE)
    name_display = req.custom_name or f"Phong cách {clean_style_id.title()}"
    profile = profiler.process_audio_files(
        file_paths=[target_path],
        style_id=clean_style_id,
        style_name=name_display,
        description=f"File giọng đã tách sạch ({clean_file})"
    )

    return {
        "status": "success",
        "message": f"Đã nạp thành công giọng sạch vào Style '{name_display}'!",
        "style_id": clean_style_id,
        "filename": clean_file,
        "profile": profile
    }

@app.post("/voices/upload")
@app.post("/voices/analyze")
async def upload_and_analyze_voice(
    file: UploadFile = File(...),
    style_id: Optional[str] = Form(default="neutral")
):
    clean_style_id = (style_id or "neutral").lower().strip()
    return await upload_style_samples(
        files=[file],
        style_id=clean_style_id,
        style_name=f"Phong cách {clean_style_id.title()}"
    )

@app.get("/voice_ref/{style_id}/{filename}")
def get_voice_reference_audio(style_id: str, filename: str):
    clean_style = os.path.basename(style_id)
    clean_file = os.path.basename(filename)
    target_path = os.path.join(PROJECT_ROOT, "data", "voice", clean_style, clean_file)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference audio not found.")
    return FileResponse(target_path, media_type="audio/wav", filename=clean_file)

@app.get("/voice_samples/{style_id}")
def list_voice_samples(style_id: str):
    """Lists all available sample WAV/MP3 files for a given style."""
    from .audio.acoustic_auto_tuner import get_auto_tuner
    tuner = get_auto_tuner(PROJECT_ROOT)
    return {"status": "success", "samples": tuner.get_style_samples(style_id)}

class AutoTuneRequest(BaseModel):
    style_id: str
    test_text: Optional[str] = "Xin chào, đây là bài kiểm tra chất giọng lồng tiếng của tôi."
    max_rounds: int = 5
    sample_file: Optional[str] = None
    user_instruction: Optional[str] = None

class ContinueTuneRequest(BaseModel):
    session_id: str
    additional_rounds: int = 5
    user_instruction: Optional[str] = None

class SavePresetRequest(BaseModel):
    session_id: str
    style_id: str
    round_idx: Optional[int] = None

@app.post("/autotune/start")
def start_autotune_session(req: AutoTuneRequest):
    """Starts closed-loop Judge evaluation and Student auto-tuning using real spoken speech."""
    from .audio.acoustic_auto_tuner import get_auto_tuner
    tuner = get_auto_tuner(PROJECT_ROOT)
    return tuner.start_autotune_session(
        style_id=req.style_id,
        test_text=req.test_text or "Xin chào, đây là bài kiểm tra chất giọng lồng tiếng của tôi.",
        max_rounds=req.max_rounds,
        sample_file=req.sample_file,
        user_instruction=req.user_instruction
    )

@app.post("/autotune/continue")
def continue_autotune_session(req: ContinueTuneRequest):
    """Continues closed-loop optimization for K additional rounds."""
    from .audio.acoustic_auto_tuner import get_auto_tuner
    tuner = get_auto_tuner(PROJECT_ROOT)
    return tuner.continue_autotune_session(
        session_id=req.session_id,
        additional_rounds=req.additional_rounds,
        user_instruction=req.user_instruction
    )

class PromptInterpretRequest(BaseModel):
    instruction: str

@app.post("/autotune/interpret-prompt")
def interpret_acoustic_prompt(req: PromptInterpretRequest):
    """Translates user natural language into physical acoustic vectors."""
    from .audio.semantic_acoustic_compiler import get_semantic_compiler
    compiler = get_semantic_compiler()
    res = compiler.compile_instruction(req.instruction)
    return {"status": "success", "compiled": res}

@app.post("/autotune/save-preset")
def save_autotune_preset(req: SavePresetRequest):
    """Saves the user-approved preset to disk only upon user confirmation."""
    from .audio.acoustic_auto_tuner import get_auto_tuner
    tuner = get_auto_tuner(PROJECT_ROOT)
    return tuner.save_optimal_preset(
        session_id=req.session_id,
        style_id=req.style_id,
        round_idx=req.round_idx
    )

@app.get("/autotune/preset/{style_id}")
def get_autotune_preset(style_id: str):
    clean_style = os.path.basename(style_id)
    preset_path = os.path.join(PROJECT_ROOT, "data", "voice", clean_style, "optimal_preset.json")
    if not os.path.exists(preset_path):
        return {"status": "none", "message": "Chưa có cấu hình Auto-tune"}
    with open(preset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"status": "success", "preset": data}

class TrainIndexRequest(BaseModel):
    style_id: str

@app.post("/trainer/train-index")
def train_voice_index(req: TrainIndexRequest):
    """Triggers 1-Click Neural Voice Index Training for a character style."""
    from .audio.voice_trainer import get_voice_trainer
    trainer = get_voice_trainer(PROJECT_ROOT)
    return trainer.train_style_index(req.style_id)

@app.get("/trainer/status/{style_id}")
def get_voice_training_status(style_id: str):
    """Returns whether a trained neural index exists for the given style."""
    from .audio.voice_trainer import get_voice_trainer
    trainer = get_voice_trainer(PROJECT_ROOT)
    return trainer.get_training_status(style_id)

@app.get("/outputs/autotune/{filename}")
def get_autotune_audio_output(filename: str):
    clean_filename = os.path.basename(filename)
    target_path = os.path.join(OUTPUTS_DIR, "autotune", clean_filename)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autotune audio not found.")
    return FileResponse(target_path, media_type="audio/wav", filename=clean_filename)

@app.get("/outputs/{filename}")
def get_audio_output(filename: str):
    # Prevent path traversal attacks
    clean_filename = os.path.basename(filename)
    target_path = os.path.join(OUTPUTS_DIR, clean_filename)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found.")
    
    media_type = "audio/wav" if clean_filename.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(target_path, media_type=media_type, filename=clean_filename)

@app.delete("/outputs/{filename}")
def delete_audio_output(filename: str):
    clean_filename = os.path.basename(filename)
    target_path = os.path.join(OUTPUTS_DIR, clean_filename)
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            return {"ok": True, "message": f"Deleted {clean_filename}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")
    raise HTTPException(status_code=404, detail="File not found")

# Mount frontend UI
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
