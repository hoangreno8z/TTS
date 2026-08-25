"""Audio Enhancer & Studio Anti-Crackling DSP Filter.
Removes digital aliasing, buzzing, clicks, and radio distortion
using Butterworth 4th order bandpass and spectral smoothing.
"""
import numpy as np
import scipy.signal

class AudioEnhancer:
    @staticmethod
    def clean_and_polish_audio(
        audio: np.ndarray,
        sr: int = 40000,
        low_cut_hz: float = 65.0,
        high_cut_hz: float = 16000.0,
        de_hum: bool = True,
        normalize_peak: float = 0.96
    ) -> np.ndarray:
        """Applies studio anti-crackling filtering, DC removal, and peak normalization."""
        if audio is None or len(audio) == 0:
            return audio

        out = audio.astype(np.float32)

        # 1. Remove DC offset
        out = out - np.mean(out)

        # 2. 4th-Order Butterworth Bandpass Filter (Cuts rumble <65Hz & aliasing >16kHz)
        nyq = 0.5 * sr
        low = max(20.0, low_cut_hz) / nyq
        high = min(nyq - 100.0, high_cut_hz) / nyq
        if 0 < low < high < 1.0:
            b, a = scipy.signal.butter(4, [low, high], btype='band')
            out = scipy.signal.filtfilt(b, a, out)

        # 3. De-Hum Notch Filter at 50Hz / 60Hz powerline noise if requested
        if de_hum:
            for freq in (50.0, 60.0, 100.0, 120.0):
                if freq < nyq:
                    q = 30.0
                    b_notch, a_notch = scipy.signal.iirnotch(freq, q, sr)
                    out = scipy.signal.filtfilt(b_notch, a_notch, out)

        # 4. Soft High-Frequency Harmonic Smoothing (Removes metallic harshness/rè)
        kernel = np.array([0.05, 0.9, 0.05], dtype=np.float32)
        out = np.convolve(out, kernel, mode='same')

        # 5. Peak Normalization
        max_val = np.max(np.abs(out))
        if max_val > 1e-5:
            out = out / max_val * normalize_peak

        return out.astype(np.float32)
