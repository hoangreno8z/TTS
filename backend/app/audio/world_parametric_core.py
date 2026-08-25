"""LAPQUE V7 — CORE 1: PARAMETRIC VOICE STYLE ENGINE (STRICT 0-AI).
Operates purely on Fourier Analysis (STFT/iFFT), WORLD Vocoder (F0, SP, AP),
MCEP (Mel-Cepstral Coefficients) & VTLN (Vocal Tract Length Normalization) Formant Warping,
and Vietnamese Prosodic State Vector P.
Zero Neural Inference at runtime — 100% CPU/WASM compatible, deterministic, 0-dong cost.
"""
import os
import math
import numpy as np
import scipy.fft as fft
import pyworld
from typing import Dict, Any, Tuple, Optional, List

class WorldParametricCore:
    """Core 1: Parametric analysis, MCEP/VTLN transformation, and WORLD iFFT synthesis."""

    def __init__(self, sample_rate: int = 24000, frame_period: float = 5.0):
        self.sample_rate = sample_rate
        self.frame_period = frame_period # ms

    def analyze(self, audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract F0, Spectral Envelope (SP), and Aperiodicity (AP) using WORLD."""
        if audio.dtype != np.float64:
            audio = audio.astype(np.float64)
        
        # 1. Harvest F0 estimator with refined refinement (StoneMask)
        f0, time_axis = pyworld.harvest(audio, self.sample_rate, frame_period=self.frame_period)
        f0 = pyworld.stonemask(audio, f0, time_axis, self.sample_rate)

        # 2. CheapTrick Spectral Envelope extraction
        sp = pyworld.cheaptrick(audio, f0, time_axis, self.sample_rate)

        # 3. D4C Aperiodicity extraction
        ap = pyworld.d4c(audio, f0, time_axis, self.sample_rate)

        return f0, sp, ap

    def synthesize(self, f0: np.ndarray, sp: np.ndarray, ap: np.ndarray) -> np.ndarray:
        """Synthesize waveform from F0, SP, AP via WORLD Inverse Fourier Transform."""
        y = pyworld.synthesize(f0, sp, ap, self.sample_rate, frame_period=self.frame_period)
        return y.astype(np.float32)

    def test_reconstruction_g1(self, audio: np.ndarray) -> Dict[str, float]:
        """Gate G1: Test reconstruction fidelity (Original -> Analysis -> Synthesis)."""
        f0, sp, ap = self.analyze(audio)
        rec = self.synthesize(f0, sp, ap)
        
        min_len = min(len(audio), len(rec))
        orig_clip = audio[:min_len]
        rec_clip = rec[:min_len]

        # F0 RMSE on voiced frames
        voiced_idx = f0 > 0
        f0_rmse = 0.0
        if np.any(voiced_idx):
            f0_rec, _ = pyworld.harvest(rec_clip.astype(np.float64), self.sample_rate, frame_period=self.frame_period)
            min_f0 = min(len(f0), len(f0_rec))
            voiced_mask = (f0[:min_f0] > 0) & (f0_rec[:min_f0] > 0)
            if np.any(voiced_mask):
                f0_rmse = float(np.sqrt(np.mean((f0[:min_f0][voiced_mask] - f0_rec[:min_f0][voiced_mask]) ** 2)))

        # Spectral Distortion (MCD proxy in dB)
        log_sp_orig = np.log(np.maximum(sp, 1e-8))
        _, sp_rec, _ = self.analyze(rec_clip)
        min_sp = min(len(sp), len(sp_rec))
        log_sp_rec = np.log(np.maximum(sp_rec[:min_sp], 1e-8))
        
        mcd = float(np.mean(np.sqrt(2.0 * np.sum((log_sp_orig[:min_sp] - log_sp_rec) ** 2, axis=1))) * (10.0 / np.log(10.0)))
        
        return {
            "g1_f0_rmse_hz": round(f0_rmse, 2),
            "g1_mcd_db": round(mcd, 2),
            "g1_passed": bool(mcd <= 6.5)
        }

    @staticmethod
    def sp_to_mcep(sp: np.ndarray, num_coeffs: int = 24) -> np.ndarray:
        """Convert Spectral Envelope (SP) to Mel-Cepstral Coefficients (MCEP) via DCT."""
        log_sp = np.log(np.maximum(sp, 1e-8))
        # Discrete Cosine Transform Type-II across frequency bins
        mcep = fft.dct(log_sp, type=2, axis=-1, norm='ortho')[:, :num_coeffs]
        return mcep

    @staticmethod
    def mcep_to_sp(mcep: np.ndarray, num_freq_bins: int) -> np.ndarray:
        """Reconstruct Spectral Envelope (SP) from MCEP via Inverse DCT."""
        padded = np.zeros((mcep.shape[0], num_freq_bins), dtype=np.float64)
        padded[:, :mcep.shape[1]] = mcep
        log_sp = fft.idct(padded, type=2, axis=-1, norm='ortho')
        sp = np.exp(log_sp)
        return sp

    @staticmethod
    def apply_vtln_warping(sp: np.ndarray, warp_alpha: float = 0.90) -> np.ndarray:
        """Apply Vocal Tract Length Normalization (VTLN) Formant Warping on Spectral Envelope.
        warp_alpha < 1.0 shifts formants higher (younger/lively character timbre, e.g. Loc Dinh Ky).
        warp_alpha > 1.0 shifts formants lower (deeper male chest resonance).
        """
        num_frames, num_bins = sp.shape
        warped_sp = np.zeros_like(sp)
        freq_grid = np.linspace(0.0, 1.0, num_bins)

        # Bilinear all-pass frequency warping function
        # w_new = w + 2.0 * arctan( (1-alpha)*sin(w) / ( (1+alpha)*cos(w) - 2*alpha ) )
        for i in range(num_bins):
            w = freq_grid[i] * np.pi
            tan_half = np.tan(w / 2.0)
            warped_w = 2.0 * np.arctan(((1.0 - warp_alpha) / (1.0 + warp_alpha)) * tan_half) if (1.0 + warp_alpha) != 0 else w
            warped_w = max(0.0, min(np.pi, warped_w))
            orig_bin = int((warped_w / np.pi) * (num_bins - 1))
            warped_sp[:, i] = sp[:, min(num_bins - 1, max(0, orig_bin))]

        return warped_sp

    def transform_style(
        self,
        audio: np.ndarray,
        pitch_shift_semitones: float = 3.66,
        vtln_alpha: float = 0.88,
        energy_scale: float = 1.15,
        speed_factor: float = 1.05
    ) -> np.ndarray:
        """Apply Joint Vietnamese Prosodic State Vector P + VTLN Formant Warping on Base Audio."""
        f0, sp, ap = self.analyze(audio)

        # 1. Prosodic Vector P: F0 Pitch Contour Transformation
        if abs(pitch_shift_semitones) > 0.05:
            pitch_ratio = 2.0 ** (pitch_shift_semitones / 12.0)
            # Transform voiced frames while preserving unvoiced regions
            voiced = f0 > 0
            f0[voiced] = f0[voiced] * pitch_ratio

        # 2. Spectral Filter Transformation: VTLN Formant Warping
        if abs(vtln_alpha - 1.0) > 0.01:
            sp = self.apply_vtln_warping(sp, warp_alpha=vtln_alpha)

        # 3. Energy & Spectral Tilt Boost (Mid-presence enhancement)
        sp = sp * energy_scale
        
        # 4. Synthesize transformed acoustic state back into Waveform via iFFT
        transformed_wav = self.synthesize(f0, sp, ap)

        # 5. Peak limiter
        max_v = np.max(np.abs(transformed_wav))
        if max_v > 0.01:
            transformed_wav = (transformed_wav / max_v) * 0.94

        return transformed_wav
