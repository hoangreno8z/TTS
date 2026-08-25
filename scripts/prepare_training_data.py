"""Prepare and slice raw reference audio into dataset segments for RVC / GPT-SoVITS training."""
import os
import sys
import math
import wave
import struct
import numpy as np
import soundfile as sf

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_SEGMENTS_DIR = os.path.join(DATA_DIR, "training_segments_loc_dinh_ky")

def prepare_dataset(input_wav_path: str, target_sr: int = 40000, min_sec: float = 2.0, max_sec: float = 10.0):
    if not os.path.exists(input_wav_path):
        print(f"Error: Input file not found at {input_wav_path}")
        return

    os.makedirs(OUTPUT_SEGMENTS_DIR, exist_ok=True)

    print(f"-> Reading reference audio from: {input_wav_path}")
    data, sr = sf.read(input_wav_path)
    if len(data.shape) > 1:
        data = np.mean(data, axis=1) # Convert to mono

    total_duration = len(data) / float(sr)
    print(f"-> Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes) at {sr} Hz")

    # Resample to target sample rate (e.g. 40kHz for RVC v2)
    if sr != target_sr:
        import scipy.signal
        num_samples = int(len(data) * float(target_sr) / sr)
        data = scipy.signal.resample(data, num_samples)
        sr = target_sr
        print(f"-> Resampled to {target_sr} Hz")

    # Energy-based voice activity detection (VAD) slicing
    frame_size = int(0.03 * sr) # 30ms frames
    hop_size = int(0.015 * sr)  # 15ms hop
    num_frames = (len(data) - frame_size) // hop_size

    rms = np.zeros(num_frames)
    for i in range(num_frames):
        start = i * hop_size
        frame = data[start : start + frame_size]
        rms[i] = np.sqrt(np.mean(frame**2))

    # Threshold for silence
    threshold = np.percentile(rms, 25) * 1.5
    is_speech = rms > threshold

    # Group speech segments
    min_samples = int(min_sec * sr)
    max_samples = int(max_sec * sr)
    silence_margin = int(0.3 * sr) # 300ms silence margin

    segments = []
    current_start = 0
    in_segment = False

    for i in range(num_frames):
        sample_idx = i * hop_size
        if is_speech[i] and not in_segment:
            in_segment = True
            current_start = max(0, sample_idx - silence_margin)
        elif not is_speech[i] and in_segment:
            segment_len = sample_idx - current_start
            if segment_len >= min_samples:
                end_idx = min(len(data), sample_idx + silence_margin)
                segments.append((current_start, end_idx))
                in_segment = False
            elif segment_len >= max_samples:
                segments.append((current_start, sample_idx))
                in_segment = False

    if in_segment and (len(data) - current_start) >= min_samples:
        segments.append((current_start, len(data)))

    print(f"-> Sliced into {len(segments)} valid training segments (2s - 10s each).")

    # Export sliced WAV files
    total_valid_sec = 0.0
    for idx, (s, e) in enumerate(segments):
        chunk = data[s:e]
        # Peak normalize to -1.0 dB
        max_val = np.max(np.abs(chunk))
        if max_val > 0.001:
            chunk = chunk / max_val * 0.9

        out_name = f"loc_dinh_ky_{idx+1:04d}.wav"
        out_path = os.path.join(OUTPUT_SEGMENTS_DIR, out_name)
        sf.write(out_path, chunk.astype(np.float32), sr)
        total_valid_sec += len(chunk) / float(sr)

    print(f"-> Saved {len(segments)} files to {OUTPUT_SEGMENTS_DIR}")
    print(f"-> Total clean training speech duration: {total_valid_sec:.2f} seconds ({total_valid_sec/60:.2f} minutes)")

    # Create zip archive for 1-click upload to Colab
    import zipfile
    zip_path = os.path.join(DATA_DIR, "dataset_loc_dinh_ky_40k.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUTPUT_SEGMENTS_DIR):
            for file in files:
                if file.endswith('.wav'):
                    zipf.write(os.path.join(root, file), arcname=file)
    print(f"-> Created 1-Click Training Package: {zip_path} ({os.path.getsize(zip_path)/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    raw_path = os.path.join(DATA_DIR, "voice", "neutral", "reference.wav")
    if not os.path.exists(raw_path):
        raw_path = os.path.join(DATA_DIR, "voice", "lali5", "reference.wav")
    prepare_dataset(raw_path)
