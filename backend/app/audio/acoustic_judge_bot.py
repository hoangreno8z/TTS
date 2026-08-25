import os
import json
import numpy as np
import soundfile as sf
import librosa
from typing import Dict, Any, List, Optional, Tuple

class AcousticJudgeBot:
    def __init__(self, target_audio_path: Optional[str] = None, profile_dict: Optional[Dict[str, Any]] = None):
        self.sr = 24000
        self.target_metrics = {}
        self.target_embedding = None
        self._hubert_model = None

        if target_audio_path and os.path.exists(target_audio_path):
            self.load_target_from_audio(target_audio_path)
        elif profile_dict:
            self.load_target_from_profile(profile_dict)

    def _get_hubert_model(self):
        if self._hubert_model is None:
            try:
                import torch
                from app.audio.rvc_inference_engine import rvc_engine
                if rvc_engine and rvc_engine.hubert_model is not None:
                    self._hubert_model = rvc_engine.hubert_model
            except Exception:
                pass
        return self._hubert_model

    def load_target_from_audio(self, audio_path: str):
        data, sr = sf.read(audio_path)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        if sr != self.sr:
            data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=self.sr)

        self.target_metrics = self._extract_audio_metrics(data, self.sr)
        self.target_embedding = self._extract_embedding(data, self.sr)

    def load_target_from_profile(self, profile: Dict[str, Any]):
        f0_stats = profile.get('f0_statistics', {})
        formants = profile.get('formants', {})
        bands = profile.get('sub_band_energy', {})

        self.target_metrics = {
            'f0_mean': f0_stats.get('f0_mean_hz', 220.0),
            'f0_std': f0_stats.get('f0_std_hz', 35.0),
            'f0_min': f0_stats.get('f0_min_hz', 100.0),
            'f0_max': f0_stats.get('f0_max_hz', 350.0),
            'F1': formants.get('F1_hz', 450.0),
            'F2': formants.get('F2_hz', 1750.0),
            'F3': formants.get('F3_hz', 2900.0),
            'F4': formants.get('F4_hz', 4500.0),
            'sub_band_energy': {
                'sub': bands.get('low_sub_ratio', 0.25),
                'mid': bands.get('mid_ratio', 0.45),
                'formant': bands.get('formant_clarity_ratio', 0.20),
                'air': bands.get('air_ratio', 0.10)
            },
            'hnr': 18.0,
            'spectral_flatness': 0.015
        }

    def _extract_embedding(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Extracts 256-D normalized acoustic embedding vector."""
        try:
            mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, n_fft=1024, hop_length=256)
            mel_db = librosa.power_to_db(mel, ref=np.max)
            mel_mean = np.mean(mel_db, axis=1)
            mel_std = np.std(mel_db, axis=1)

            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
            mfcc_delta = librosa.feature.delta(mfcc)
            mfcc_feat = np.concatenate([np.mean(mfcc, axis=1), np.mean(mfcc_delta, axis=1)])

            contrast = np.mean(librosa.feature.spectral_contrast(y=audio, sr=sr), axis=1)
            try:
                harmonic_y = librosa.effects.harmonic(audio)
                tonnetz = np.mean(librosa.feature.tonnetz(y=harmonic_y, sr=sr), axis=1)
            except Exception:
                tonnetz = np.zeros(6)

            cent = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
            spec_stats = np.array([cent / 5000.0, rolloff / 5000.0, zcr * 10.0])

            vec = np.concatenate([mel_mean, mel_std, mfcc_feat, contrast, tonnetz, spec_stats])
            vec = vec[:256]
            if len(vec) < 256:
                vec = np.pad(vec, (0, 256 - len(vec)))
            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec = vec / norm
            return vec.astype(np.float32)
        except Exception:
            return np.zeros(256, dtype=np.float32)

    def _extract_audio_metrics(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        f0_mean, f0_std, f0_min, f0_max = 200.0, 30.0, 100.0, 300.0
        try:
            import pyworld as pw
            audio_f64 = audio.astype(np.float64)
            _f0, _t = pw.harvest(audio_f64, sr, f0_floor=65.0, f0_ceil=550.0)
            f0_active = _f0[_f0 > 0]
            if len(f0_active) > 10:
                f0_mean = float(np.mean(f0_active))
                f0_std = float(np.std(f0_active))
                f0_min = float(np.percentile(f0_active, 5))
                f0_max = float(np.percentile(f0_active, 95))
        except Exception:
            f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=65, fmax=550, sr=sr)
            f0_active = f0[~np.isnan(f0)]
            if len(f0_active) > 10:
                f0_mean = float(np.mean(f0_active))
                f0_std = float(np.std(f0_active))
                f0_min = float(np.min(f0_active))
                f0_max = float(np.max(f0_active))

        stft = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512))
        spec_env = np.mean(stft, axis=1)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

        def find_peak_in_range(low_f, high_f, default_f):
            mask = (freqs >= low_f) & (freqs <= high_f)
            if not np.any(mask):
                return default_f
            sub_env = spec_env[mask]
            sub_freqs = freqs[mask]
            peak_idx = np.argmax(sub_env)
            return float(sub_freqs[peak_idx])

        F1 = find_peak_in_range(200, 950, 450.0)
        F2 = find_peak_in_range(1000, 2400, 1750.0)
        F3 = find_peak_in_range(2450, 3800, 2900.0)
        F4 = find_peak_in_range(3850, 6000, 4500.0)

        total_energy = np.sum(spec_env) + 1e-8
        sub_mask = freqs <= 350
        mid_mask = (freqs > 350) & (freqs <= 2000)
        formant_mask = (freqs > 2000) & (freqs <= 6000)
        air_mask = freqs > 6000

        sub_ratio = float(np.sum(spec_env[sub_mask]) / total_energy)
        mid_ratio = float(np.sum(spec_env[mid_mask]) / total_energy)
        formant_ratio = float(np.sum(spec_env[formant_mask]) / total_energy)
        air_ratio = float(np.sum(spec_env[air_mask]) / total_energy)

        flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio)))
        
        autocorr = np.correlate(audio[:min(len(audio), sr)], audio[:min(len(audio), sr)], mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        if len(autocorr) > 100:
            peak_val = np.max(autocorr[30:400]) if len(autocorr) > 400 else np.max(autocorr[30:])
            zero_val = autocorr[0] + 1e-8
            hnr_val = float(10 * np.log10(max(1e-4, peak_val / (zero_val - peak_val + 1e-4))))
        else:
            hnr_val = 15.0

        return {
            'f0_mean': f0_mean,
            'f0_std': f0_std,
            'f0_min': f0_min,
            'f0_max': f0_max,
            'F1': F1,
            'F2': F2,
            'F3': F3,
            'F4': F4,
            'sub_band_energy': {
                'sub': sub_ratio,
                'mid': mid_ratio,
                'formant': formant_ratio,
                'air': air_ratio
            },
            'hnr': hnr_val,
            'spectral_flatness': flatness,
            'mfcc': np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20), axis=1)
        }

    def evaluate_audio(
        self,
        candidate_audio: np.ndarray,
        sr: int = 24000,
        user_instruction: Optional[str] = ""
    ) -> Dict[str, Any]:
        if sr != self.sr:
            candidate_audio = librosa.resample(candidate_audio.astype(np.float32), orig_sr=sr, target_sr=self.sr)

        cand_metrics = self._extract_audio_metrics(candidate_audio, self.sr)
        cand_embedding = self._extract_embedding(candidate_audio, self.sr)
        tgt = self.target_metrics

        critique_notes = []
        delta_corrections = {}
        instruction = (user_instruction or "").lower().strip()

        # Instruction modifiers
        user_pitch_bias = 0.0
        user_sub_bias = 0.0
        user_air_bias = 0.0
        if "trầm" in instruction or "sâu" in instruction or "ấm" in instruction:
            user_pitch_bias -= 2.0
            user_sub_bias += 2.5
            critique_notes.append("💡 Giám khảo ghi nhận nhắc nhở: Tăng cường độ trầm ấm theo yêu cầu.")
        if "cao" in instruction or "thanh" in instruction:
            user_pitch_bias += 2.0
            critique_notes.append("💡 Giám khảo ghi nhận nhắc nhở: Tăng cao độ thanh thoát theo yêu cầu.")
        if "trong" in instruction or "bớt rè" in instruction or "sạch" in instruction:
            critique_notes.append("💡 Giám khảo ghi nhận nhắc nhở: Ưu tiên lọc nhiễu dải cao.")
        if "bớt the thé" in instruction or "giảm treble" in instruction:
            user_air_bias -= 3.0

        # 1. Timbre Embedding Score (Max 20.0)
        if self.target_embedding is not None and cand_embedding is not None:
            cos_sim = float(np.dot(self.target_embedding, cand_embedding))
            cos_sim = max(0.0, min(1.0, cos_sim))
            timbre_score = cos_sim * 20.0
            critique_notes.append(f"Âm sắc đặc trưng ContentVec: đạt {cos_sim*100:.1f}% tương đồng.")
        else:
            tgt_mfcc = tgt.get('mfcc', np.zeros(20))
            cand_mfcc = cand_metrics.get('mfcc', np.zeros(20))
            dist = float(np.linalg.norm(tgt_mfcc - cand_mfcc))
            cos_sim = max(0.0, min(1.0, 1.0 - (dist / 40.0)))
            timbre_score = max(5.0, 20.0 * cos_sim)
            critique_notes.append(f"Âm sắc đặc trưng MFCC: đạt {cos_sim*100:.1f}% tương đồng.")

        # 2. Spectral Envelope Correlation (Max 15.0)
        tgt_mfcc = tgt.get('mfcc', np.zeros(20))
        cand_mfcc = cand_metrics.get('mfcc', np.zeros(20))
        corr = 0.8
        if len(tgt_mfcc) > 0 and len(cand_mfcc) > 0:
            c_mat = np.corrcoef(tgt_mfcc, cand_mfcc)
            if not np.isnan(c_mat[0, 1]):
                corr = max(0.0, min(1.0, (c_mat[0, 1] + 1.0) / 2.0))
        spectral_envelope_score = max(3.0, corr * 15.0)

        # 3. Pitch Mean F0 (Max 15.0)
        tgt_f0 = tgt.get('f0_mean', 220.0)
        cand_f0 = cand_metrics.get('f0_mean', 220.0)
        if tgt_f0 > 0 and cand_f0 > 0:
            semitone_diff = 12.0 * np.log2(cand_f0 / tgt_f0) + user_pitch_bias
        else:
            semitone_diff = 0.0
        f0_error = abs(semitone_diff)
        pitch_mean_score = max(0.0, 15.0 - (f0_error * 2.5))
        delta_corrections['pitch_shift_semitones'] = float(-semitone_diff)

        if f0_error < 0.35:
            critique_notes.append(f"Cao độ F0 rất chuẩn (lệch chỉ {semitone_diff:+.2f} nốt).")
        elif semitone_diff > 0:
            critique_notes.append(f"Cao độ F0 thừa +{semitone_diff:.1f} nốt (cần hạ thấp).")
        else:
            critique_notes.append(f"Cao độ F0 thiếu {semitone_diff:.1f} nốt (cần nâng cao).")

        # 4. Pitch Dynamics / Intonation STD (Max 10.0)
        tgt_std = tgt.get('f0_std', 30.0)
        cand_std = cand_metrics.get('f0_std', 30.0)
        std_diff = cand_std - tgt_std
        pitch_dynamics_score = max(2.0, 10.0 - (abs(std_diff) / max(10.0, tgt_std)) * 8.0)
        delta_corrections['pitch_dynamics_factor'] = float(tgt_std / max(5.0, cand_std))

        # 5. Formant F1 - Jaw & Pharynx Resonance (Max 10.0)
        tgt_f1 = tgt.get('F1', 450.0)
        cand_f1 = cand_metrics.get('F1', 450.0)
        f1_diff = cand_f1 - tgt_f1
        f1_err_ratio = abs(f1_diff) / max(100.0, tgt_f1)
        formant_f1_score = max(1.0, 10.0 * (1.0 - f1_err_ratio * 2.0))
        if abs(f1_diff) > 30:
            critique_notes.append(f"Formant F1 lệch {f1_diff:+.0f}Hz ({'thừa' if f1_diff > 0 else 'thiếu'}).")

        # 6. Formant F2 - Tongue & Midrange Balance (Max 10.0)
        tgt_f2 = tgt.get('F2', 1750.0)
        cand_f2 = cand_metrics.get('F2', 1750.0)
        f2_diff = cand_f2 - tgt_f2
        f2_err_ratio = abs(f2_diff) / max(200.0, tgt_f2)
        formant_f2_score = max(1.0, 10.0 * (1.0 - f2_err_ratio * 2.0))
        delta_corrections['formant_warp_ratio'] = float(1.0 - (f2_diff / 3500.0))
        if abs(f2_diff) > 60:
            critique_notes.append(f"Formant F2 lệch {f2_diff:+.0f}Hz ({'thừa' if f2_diff > 0 else 'thiếu'}).")

        # 7. Formant F3-F4 Head & Identity Resonance (Max 5.0)
        tgt_f3 = tgt.get('F3', 2900.0)
        cand_f3 = cand_metrics.get('F3', 2900.0)
        f3_err_ratio = abs(cand_f3 - tgt_f3) / max(300.0, tgt_f3)
        formant_f3_f4_score = max(1.0, 5.0 * (1.0 - f3_err_ratio * 1.8))

        # 8. HNR Clarity & Voice Quality (Max 5.0)
        cand_hnr = cand_metrics.get('hnr', 15.0)
        hnr_clarity_score = min(5.0, max(1.0, (cand_hnr / 20.0) * 5.0))

        # 9. Anti-Crackle & High Frequency Flatness (Max 5.0)
        cand_flat = cand_metrics.get('spectral_flatness', 0.02)
        anti_crackle_score = min(5.0, max(1.0, (1.0 - min(0.1, cand_flat) * 9.0) * 5.0))
        if cand_flat > 0.04:
            critique_notes.append("Phát hiện dải cao gắt/nhiễu - kích hoạt bộ lọc làm mịn.")
            delta_corrections['anti_crackle_filter'] = True

        # 10. Sub/Mid/Air Energy Balance (Max 5.0)
        tgt_bands = tgt.get('sub_band_energy', {})
        cand_bands = cand_metrics.get('sub_band_energy', {})
        sub_diff = (cand_bands.get('sub', 0.25) - tgt_bands.get('sub', 0.25))
        air_diff = (cand_bands.get('air', 0.10) - tgt_bands.get('air', 0.10))
        band_err = abs(sub_diff) + abs(air_diff)
        band_balance_score = max(1.0, 5.0 - band_err * 8.0)

        delta_corrections['eq_sub_gain_db'] = float(-sub_diff * 18.0 + user_sub_bias)
        delta_corrections['eq_air_gain_db'] = float(-air_diff * 18.0 + user_air_bias)

        total_score = float(np.clip(
            timbre_score + spectral_envelope_score + pitch_mean_score +
            pitch_dynamics_score + formant_f1_score + formant_f2_score +
            formant_f3_f4_score + hnr_clarity_score + anti_crackle_score +
            band_balance_score,
            0.0, 100.0
        ))

        return {
            'total_score': round(total_score, 1),
            'breakdown': {
                'timbre_score': round(timbre_score, 1),
                'timbre_max': 20.0,
                'spectral_envelope_score': round(spectral_envelope_score, 1),
                'spectral_envelope_max': 15.0,
                'pitch_mean_score': round(pitch_mean_score, 1),
                'pitch_mean_max': 15.0,
                'pitch_dynamics_score': round(pitch_dynamics_score, 1),
                'pitch_dynamics_max': 10.0,
                'formant_f1_score': round(formant_f1_score, 1),
                'formant_f1_max': 10.0,
                'formant_f2_score': round(formant_f2_score, 1),
                'formant_f2_max': 10.0,
                'formant_f3_f4_score': round(formant_f3_f4_score, 1),
                'formant_f3_f4_max': 5.0,
                'hnr_clarity_score': round(hnr_clarity_score, 1),
                'hnr_clarity_max': 5.0,
                'anti_crackle_score': round(anti_crackle_score, 1),
                'anti_crackle_max': 5.0,
                'band_balance_score': round(band_balance_score, 1),
                'band_balance_max': 5.0
            },
            'candidate_metrics': {
                'f0_mean_hz': round(cand_metrics['f0_mean'], 1),
                'f0_std_hz': round(cand_metrics['f0_std'], 1),
                'F1_hz': round(cand_metrics['F1'], 1),
                'F2_hz': round(cand_metrics['F2'], 1),
                'F3_hz': round(cand_metrics['F3'], 1),
                'F4_hz': round(cand_metrics['F4'], 1),
                'hnr_db': round(cand_metrics['hnr'], 1),
                'semitone_diff': round(semitone_diff, 2),
                'f1_diff_hz': round(f1_diff, 0),
                'f2_diff_hz': round(f2_diff, 0)
            },
            'critique_notes': critique_notes,
            'delta_corrections': delta_corrections,
            'verdict': 'XUẤT SẮC (ĐẠT CHUẨN 100Đ)' if total_score >= 95.0 else 'RẤT TỐT (ĐẠT PHÒNG THU)' if total_score >= 82.0 else 'CẦN TỐI ƯU THÊM'
        }
