"""Fourier Transform Spectral Engine (STFT / iSTFT / Phase Vocoder).
Implements pure mathematical Spectral Envelope Transfer and Formant Matching
based on Short-Time Fourier Transform directly on CPU with zero heavy AI overhead.
"""
import os
import math
import numpy as np
import scipy.signal
import scipy.ndimage
import soundfile as sf

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "models")):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", ".."))

class FourierSpectralEngine:
    _instance = None

    def __init__(self, n_fft: int = 2048, hop_length: int = 512, win_length: int = 2048):
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.window = np.hanning(win_length).astype(np.float32)
        self.target_spectral_envelope = None
        self.target_sr = 24000
        self.is_calibrated = False
        self._calibrate_from_reference()

    def _calibrate_from_reference(self):
        """Extract reference spectral fingerprint from target audio using STFT."""
        ref_path = os.path.join(PROJECT_ROOT, "data", "voice", "neutral", "reference.wav")
        if not os.path.exists(ref_path):
            return

        try:
            audio, sr = sf.read(ref_path)
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Resample to 24kHz for consistent Fourier analysis
            if sr != self.target_sr:
                num_samples = int(len(audio) * float(self.target_sr) / sr)
                audio = scipy.signal.resample(audio, num_samples)

            # Compute STFT magnitude spectrum
            f, t, Zxx = scipy.signal.stft(
                audio,
                fs=self.target_sr,
                window='hann',
                nperseg=self.win_length,
                noverlap=self.win_length - self.hop_length,
                nfft=self.n_fft
            )
            mag = np.abs(Zxx)  # [freq_bins, time_frames]
            
            # Average power spectral density
            mean_spectrum = np.mean(mag, axis=1)  # [freq_bins]
            
            # Extract smooth spectral envelope using median filter + Gaussian smoothing (Cepstral equivalent)
            smooth_env = scipy.ndimage.gaussian_filter1d(mean_spectrum, sigma=4.0)
            smooth_env = np.maximum(smooth_env, 1e-6)
            
            # Normalize energy
            self.target_spectral_envelope = smooth_env / np.mean(smooth_env)
            self.is_calibrated = True
            print(f"-> Fourier Spectral Engine Calibrated ({len(self.target_spectral_envelope)} frequency bins)!")
        except Exception as e:
            print(f"-> Error calibrating Fourier Spectral Engine: {e}")

    def apply_spectral_transfer(
        self,
        audio_float: np.ndarray,
        sr: int = 24000,
        morph_strength: float = 0.75,
        formant_boost_db: float = 2.5
    ) -> np.ndarray:
        """Transform input audio by matching its STFT spectral envelope to target voice."""
        if not self.is_calibrated or self.target_spectral_envelope is None:
            return audio_float

        try:
            # Resample input if needed
            orig_sr = sr
            if orig_sr != self.target_sr:
                num_samples = int(len(audio_float) * float(self.target_sr) / orig_sr)
                audio = scipy.signal.resample(audio_float, num_samples)
            else:
                audio = audio_float.copy()

            # 1. Short-Time Fourier Transform (STFT)
            f, t, Zxx = scipy.signal.stft(
                audio,
                fs=self.target_sr,
                window='hann',
                nperseg=self.win_length,
                noverlap=self.win_length - self.hop_length,
                nfft=self.n_fft
            )
            
            mag = np.abs(Zxx)
            phase = np.angle(Zxx)

            # 2. Extract current source spectral envelope across frames
            src_env = scipy.ndimage.gaussian_filter1d(mag, sigma=4.0, axis=0)
            src_env = np.maximum(src_env, 1e-6)

            # 3. Compute Fourier Transfer Function H(f, t)
            target_env_2d = self.target_spectral_envelope[:, np.newaxis]
            # Normalize source envelope per frame
            src_mean = np.mean(src_env, axis=0, keepdims=True)
            src_norm_env = src_env / np.maximum(src_mean, 1e-6)

            # Ratio of target to source envelope
            ratio = target_env_2d / np.maximum(src_norm_env, 1e-6)
            # Clamp ratio to prevent excessive amplification
            ratio = np.clip(ratio, 0.25, 4.0)

            # Interpolate based on morph strength
            transfer_gain = 1.0 + morph_strength * (ratio - 1.0)

            # 4. Formant Enhancement in 1.5kHz - 3.5kHz region (Chau Tinh Tri clarity band)
            freq_bins = f
            formant_mask = (freq_bins >= 1500) & (freq_bins <= 3500)
            gain_multiplier = 10.0 ** (formant_boost_db / 20.0)
            transfer_gain[formant_mask, :] *= (1.0 + morph_strength * (gain_multiplier - 1.0))

            # 5. Apply Transfer in Fourier Domain
            mag_modified = mag * transfer_gain

            # Reconstruct complex spectrum with preserved phase
            Zxx_modified = mag_modified * np.exp(1j * phase)

            # 6. Inverse Short-Time Fourier Transform (iSTFT)
            _, y_out = scipy.signal.istft(
                Zxx_modified,
                fs=self.target_sr,
                window='hann',
                nperseg=self.win_length,
                noverlap=self.win_length - self.hop_length,
                nfft=self.n_fft
            )

            # Resample back to original sample rate if needed
            if orig_sr != self.target_sr:
                num_out = int(len(y_out) * float(orig_sr) / self.target_sr)
                y_out = scipy.signal.resample(y_out, num_out)

            # Peak normalization
            max_val = np.max(np.abs(y_out))
            if max_val > 1e-6:
                y_out = y_out / max_val * 0.95

            return y_out.astype(np.float32)

        except Exception as e:
            print(f"Fourier Spectral Transfer fallback: {e}")
            return audio_float

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FourierSpectralEngine()
        return cls._instance
