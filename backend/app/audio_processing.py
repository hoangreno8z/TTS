"""Audio Preprocessing and Dataset Utilities for LAPQUE Vietnamese TTS.
Handles: WAV conversion, sample rate normalization (24kHz standard),
energy-based VAD / silence trimming, segment slicing (3-10s), and metadata generation.
Pure-Python + standard library compatible with optional numpy/scipy/soundfile/ffmpeg acceleration.
"""
import os
import wave
import struct
import math
import json
import subprocess
import shutil
from typing import List, Dict, Tuple, Optional

TARGET_SAMPLE_RATE = 24000
TARGET_CHANNELS = 1  # Mono
TARGET_SAMPLE_WIDTH = 2  # 16-bit PCM

class AudioProcessor:
    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def read_wav_pcm16(wav_path: str) -> Tuple[List[int], int, int]:
        """Read standard 16-bit PCM WAV file into integer samples."""
        with wave.open(wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

            if sampwidth != 2:
                raise ValueError(f"Only 16-bit PCM WAV is supported directly (got {sampwidth * 8}-bit). Use convert_to_wav first.")

            # Unpack 16-bit signed integers
            total_samples = n_frames * n_channels
            fmt = f"<{total_samples}h"
            samples = list(struct.unpack(fmt, raw_data))

            # If stereo, average to mono
            if n_channels == 2:
                mono_samples = []
                for i in range(0, len(samples), 2):
                    mono_samples.append((samples[i] + samples[i+1]) // 2)
                return mono_samples, framerate, 1
            return samples, framerate, n_channels

    @staticmethod
    def write_wav_pcm16(output_path: str, samples: List[int], sample_rate: int = TARGET_SAMPLE_RATE):
        """Write integer samples to a 16-bit Mono WAV file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Clip samples to 16-bit signed range [-32768, 32767]
            clipped = [max(-32768, min(32767, int(s))) for s in samples]
            data = struct.pack(f"<{len(clipped)}h", *clipped)
            wf.writeframes(data)

    @classmethod
    def convert_to_wav(cls, input_path: str, output_path: str, target_sr: int = TARGET_SAMPLE_RATE) -> str:
        """Convert any audio file (MP3, AAC, FLAC, WAV) to standard Mono 16-bit PCM WAV at target_sr."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 1. Try soundfile decoding (supports MP3, WAV, FLAC, OGG without external ffmpeg)
        try:
            import soundfile as sf
            import numpy as np
            data, sr = sf.read(input_path)
            # Downmix to mono if multi-channel
            if len(data.shape) > 1 and data.shape[1] > 1:
                data = np.mean(data, axis=1)
            elif len(data.shape) > 1 and data.shape[1] == 1:
                data = data[:, 0]
            
            if sr != target_sr:
                new_len = int(len(data) * float(target_sr) / sr)
                data = np.interp(
                    np.linspace(0, len(data), new_len, endpoint=False),
                    np.arange(len(data)),
                    data
                )

            # Convert to PCM16
            pcm16 = np.clip(data * 32767.0, -32768, 32767).astype(np.int16)
            sf.write(output_path, pcm16, target_sr, subtype='PCM_16')
            return output_path
        except Exception:
            pass

        # 2. Fallback to FFmpeg if available
        if cls.is_ffmpeg_available():
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-ac", "1",
                "-ar", str(target_sr),
                "-acodec", "pcm_s16le",
                output_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return output_path

        # 3. Native fallback for existing WAV files
        if input_path.lower().endswith(".wav"):
            samples, sr, _ = cls.read_wav_pcm16(input_path)
            if sr != target_sr:
                samples = cls.resample_linear(samples, sr, target_sr)
            cls.write_wav_pcm16(output_path, samples, target_sr)
            return output_path
            
        raise RuntimeError(f"Could not convert {input_path} to WAV.")

    @staticmethod
    def resample_linear(samples: List[int], orig_sr: int, target_sr: int) -> List[int]:
        """Simple linear interpolation resampler in pure Python."""
        if orig_sr == target_sr:
            return samples
        ratio = target_sr / orig_sr
        new_len = int(len(samples) * ratio)
        resampled = [0] * new_len
        for i in range(new_len):
            orig_idx = i / ratio
            idx0 = int(orig_idx)
            idx1 = min(idx0 + 1, len(samples) - 1)
            frac = orig_idx - idx0
            resampled[i] = int(samples[idx0] * (1 - frac) + samples[idx1] * frac)
        return resampled

    @staticmethod
    def compute_frame_energy(samples: List[int], frame_len: int) -> List[float]:
        """Calculate Root Mean Square (RMS) energy for consecutive frames."""
        energies = []
        for i in range(0, len(samples), frame_len):
            chunk = samples[i:i+frame_len]
            if not chunk:
                continue
            rms = math.sqrt(sum(s * s for s in chunk) / len(chunk)) / 32768.0
            energies.append(rms)
        return energies

    @classmethod
    def trim_silence(cls, samples: List[int], sample_rate: int = TARGET_SAMPLE_RATE, threshold: float = 0.01) -> List[int]:
        """Trim leading and trailing silence based on energy threshold."""
        frame_len = int(sample_rate * 0.02)  # 20ms frame
        energies = cls.compute_frame_energy(samples, frame_len)
        if not energies:
            return samples

        # Find start frame
        start_frame = 0
        for idx, e in enumerate(energies):
            if e > threshold:
                start_frame = max(0, idx - 2)  # Leave 40ms headroom
                break

        # Find end frame
        end_frame = len(energies) - 1
        for idx in range(len(energies) - 1, -1, -1):
            if energies[idx] > threshold:
                end_frame = min(len(energies) - 1, idx + 2)
                break

        start_sample = start_frame * frame_len
        end_sample = min(len(samples), (end_frame + 1) * frame_len)
        return samples[start_sample:end_sample]

    @classmethod
    def segment_audio(
        cls,
        samples: List[int],
        sample_rate: int = TARGET_SAMPLE_RATE,
        min_sec: float = 3.0,
        max_sec: float = 30.0,
        silence_thresh: float = 0.015
    ) -> List[List[int]]:
        """Split a long audio into optimal segments (3s to 30s) at natural pause/silence boundaries."""
        frame_len = int(sample_rate * 0.05)  # 50ms frames
        energies = cls.compute_frame_energy(samples, frame_len)
        min_frames = int(min_sec * sample_rate / frame_len)
        max_frames = int(max_sec * sample_rate / frame_len)

        segments = []
        cur_start_frame = 0
        n_frames = len(energies)

        i = 0
        while i < n_frames:
            segment_len = i - cur_start_frame
            # If we reached minimum length, check for a silence pause
            if segment_len >= min_frames:
                is_silence = energies[i] < silence_thresh
                if is_silence or segment_len >= max_frames:
                    # Found boundary
                    start_s = cur_start_frame * frame_len
                    end_s = min(len(samples), (i + 1) * frame_len)
                    seg = cls.trim_silence(samples[start_s:end_s], sample_rate)
                    if len(seg) >= int(min_sec * sample_rate * 0.8):  # Check minimum duration
                        segments.append(seg)
                    cur_start_frame = i + 1
            i += 1

        # Remaining tail
        if cur_start_frame < n_frames:
            start_s = cur_start_frame * frame_len
            seg = cls.trim_silence(samples[start_s:], sample_rate)
            if len(seg) >= int(min_sec * sample_rate * 0.8):
                segments.append(seg)

        return segments
