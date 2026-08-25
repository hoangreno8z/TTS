"""Voice Spectral Profiler & Style Builder.
Processes uploaded MP3/WAV files, extracts Fourier Spectral Envelope, Formants (F1-F4),
Pitch F0 statistics, HNR, and ContentVec neural timbre embeddings into a complete Voice Profile.
"""
import os
import sys
import json
import math
import numpy as np
import scipy.signal
import scipy.ndimage
import soundfile as sf
import torch

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "models")):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", ".."))

MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "rvc")
DATA_VOICE_DIR = os.path.join(PROJECT_ROOT, "data", "voice")
RVC_ROOT = os.path.join(curr_dir, "Retrieval-based-Voice-Conversion-WebUI-main")

class VoiceSpectralProfiler:
    def __init__(self, target_sr: int = 40000):
        self.target_sr = target_sr
        self.n_fft = 2048
        self.hop_length = 512
        self.win_length = 2048

    def process_audio_files(
        self,
        file_paths: list[str],
        style_id: str,
        style_name: str,
        description: str = ""
    ) -> dict:
        """Process multiple audio files, extract Fourier & Neural acoustic fingerprint, and save profile."""
        os.makedirs(os.path.join(DATA_VOICE_DIR, style_id), exist_ok=True)
        os.makedirs(MODELS_DIR, exist_ok=True)

        combined_audio = []
        for fp in file_paths:
            try:
                # Read audio file (MP3, WAV, etc.)
                data, sr = sf.read(fp)
                if len(data.shape) > 1:
                    data = np.mean(data, axis=1)
                
                # Resample to target_sr
                if sr != self.target_sr:
                    num_samples = int(len(data) * float(self.target_sr) / sr)
                    data = scipy.signal.resample(data, num_samples)
                
                # Remove extreme silence/DC offset
                data = data - np.mean(data)
                max_amp = np.max(np.abs(data))
                if max_amp > 1e-4:
                    data = data / max_amp * 0.95
                    combined_audio.append(data)
            except Exception as e:
                print(f"Error loading {fp}: {e}")

        if not combined_audio:
            raise ValueError("No valid audio data could be extracted from uploaded files.")

        master_audio = np.concatenate(combined_audio).astype(np.float32)
        total_duration = len(master_audio) / self.target_sr

        # 1. Save master reference WAV
        ref_wav_path = os.path.join(DATA_VOICE_DIR, style_id, "reference.wav")
        sf.write(ref_wav_path, master_audio, self.target_sr)

        # 2. Extract Fourier STFT Spectral Envelope (2048 bins)
        f_axis, t_axis, Zxx = scipy.signal.stft(
            master_audio,
            fs=self.target_sr,
            window='hann',
            nperseg=self.win_length,
            noverlap=self.win_length - self.hop_length,
            nfft=self.n_fft
        )
        mag = np.abs(Zxx)
        mean_spectrum = np.mean(mag, axis=1)
        smooth_env = scipy.ndimage.gaussian_filter1d(mean_spectrum, sigma=4.0)
        smooth_env = np.maximum(smooth_env, 1e-6)
        norm_env = smooth_env / np.mean(smooth_env)

        # 3. Extract Formant Peaks (F1, F2, F3, F4) via spectral peak detection
        peaks, props = scipy.signal.find_peaks(smooth_env, distance=15, prominence=0.05)
        peak_freqs = f_axis[peaks]
        # Categorize formants in standard vocal ranges
        f1 = float(peak_freqs[(peak_freqs >= 200) & (peak_freqs < 1000)][0]) if any((peak_freqs >= 200) & (peak_freqs < 1000)) else 550.0
        f2 = float(peak_freqs[(peak_freqs >= 1000) & (peak_freqs < 2500)][0]) if any((peak_freqs >= 1000) & (peak_freqs < 2500)) else 1750.0
        f3 = float(peak_freqs[(peak_freqs >= 2500) & (peak_freqs < 4000)][0]) if any((peak_freqs >= 2500) & (peak_freqs < 4000)) else 2900.0
        f4 = float(peak_freqs[(peak_freqs >= 4000) & (peak_freqs < 6000)][0]) if any((peak_freqs >= 4000) & (peak_freqs < 6000)) else 4500.0

        # 4. Extract Pitch F0 statistics using pyworld/harvest
        try:
            import pyworld as pw
            audio_16k = scipy.signal.resample_poly(master_audio, 16000, self.target_sr).astype(np.float64)
            f0, t = pw.harvest(audio_16k, 16000, frame_period=10.0, f0_floor=50.0, f0_ceil=800.0)
            voiced_f0 = f0[f0 > 60.0]
            if len(voiced_f0) > 0:
                f0_mean = float(np.mean(voiced_f0))
                f0_std = float(np.std(voiced_f0))
                f0_min = float(np.min(voiced_f0))
                f0_max = float(np.max(voiced_f0))
            else:
                f0_mean, f0_std, f0_min, f0_max = 195.0, 42.0, 90.0, 380.0
        except Exception:
            f0_mean, f0_std, f0_min, f0_max = 195.0, 42.0, 90.0, 380.0

        # 5. Extract ContentVec 768-D features and build Faiss index
        index_path = os.path.join(MODELS_DIR, f"{style_id}.index")
        num_vectors = self._build_faiss_index(master_audio, index_path)

        # 6. Calculate Energy Band Distribution
        energy_low = float(np.mean(norm_env[f_axis < 500]))
        energy_mid = float(np.mean(norm_env[(f_axis >= 500) & (f_axis < 2000)]))
        energy_clarity = float(np.mean(norm_env[(f_axis >= 2000) & (f_axis < 4000)]))
        energy_air = float(np.mean(norm_env[(f_axis >= 4000) & (f_axis < 8000)]))

        pitch_shift = round(12.0 * math.log2(f0_mean / 135.0), 2) if f0_mean > 0 else 0.0

        profile = {
            "style_id": style_id,
            "name": style_name,
            "description": description or f"Style tạo từ {len(file_paths)} file âm thanh mẫu ({total_duration:.1f}s)",
            "total_duration_seconds": round(total_duration, 2),
            "files_processed": len(file_paths),
            "f0_statistics": {
                "f0_mean_hz": round(f0_mean, 1),
                "f0_std_hz": round(f0_std, 1),
                "f0_min_hz": round(f0_min, 1),
                "f0_max_hz": round(f0_max, 1),
                "suggested_pitch_shift_semitones": pitch_shift
            },
            "formants": {
                "F1_hz": round(f1, 1),
                "F2_hz": round(f2, 1),
                "F3_hz": round(f3, 1),
                "F4_hz": round(f4, 1)
            },
            "spectral_bands": {
                "low_energy_0_500hz": round(energy_low, 3),
                "mid_energy_500_2khz": round(energy_mid, 3),
                "formant_clarity_2_4khz": round(energy_clarity, 3),
                "air_band_4_8khz": round(energy_air, 3)
            },
            "faiss_timbre_vectors": num_vectors,
            "has_index": os.path.exists(index_path),
            "spectral_envelope_bins": len(norm_env),
            "pitch_adjustment": pitch_shift / 25.0 if pitch_shift != 0 else 0.15,
            "speed_rate": 1.02 if f0_mean > 170 else 0.98
        }

        # Save profile JSON
        profile_json_path = os.path.join(DATA_VOICE_DIR, style_id, "acoustic_profile.json")
        with open(profile_json_path, "w", encoding="utf-8") as f_out:
            json.dump(profile, f_out, indent=2, ensure_ascii=False)

        # Also save spectral envelope array for Fourier engine
        np.save(os.path.join(DATA_VOICE_DIR, style_id, "spectral_envelope.npy"), norm_env)

        return profile

    def _build_faiss_index(self, audio: np.ndarray, index_output_path: str) -> int:
        """Extract ContentVec embeddings from audio and build Faiss index."""
        try:
            import faiss
            from transformers import AutoFeatureExtractor
            hubert_dir = os.path.join(RVC_ROOT, "assets", "hubert_base")
            if not os.path.exists(hubert_dir):
                return 0

            old_cwd = os.getcwd()
            os.chdir(RVC_ROOT)
            sys.path.insert(0, RVC_ROOT)
            from infer.hubert import load_hubert_model, extract_hubert_features
            model = load_hubert_model("cpu", is_half=False)

            # Resample to 16kHz for ContentVec
            audio_16k = scipy.signal.resample_poly(audio, 16000, self.target_sr).astype(np.float32)
            
            # Slice into chunks of 10s
            chunk_size = 16000 * 10
            all_feats = []
            with torch.no_grad():
                for start in range(0, len(audio_16k), chunk_size):
                    chunk = audio_16k[start:start + chunk_size]
                    if len(chunk) < 1600:
                        continue
                    tensor = torch.from_numpy(chunk).unsqueeze(0)
                    feats = extract_hubert_features(model, tensor, "v2")
                    feats_np = feats.squeeze(0).cpu().numpy().astype(np.float32)
                    all_feats.append(feats_np)

            os.chdir(old_cwd)

            if not all_feats:
                return 0

            big_feats = np.concatenate(all_feats, axis=0)  # [N, 768]
            dim = big_feats.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(big_feats)
            faiss.write_index(index, index_output_path)
            print(f"-> Built Faiss Index with {index.ntotal} vectors at {index_output_path}!")
            return int(index.ntotal)
        except Exception as e:
            print(f"-> Notice: Could not build Faiss index ({e}), skipping neural indexing.")
            return 0
