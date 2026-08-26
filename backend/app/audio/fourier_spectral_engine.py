import os
import glob
import math
import json
import numpy as np
import scipy.signal
import scipy.ndimage
import soundfile as sf

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, '..', '..', '..'))
if not os.path.exists(os.path.join(PROJECT_ROOT, 'models')):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, '..', '..'))

CHARACTER_PRESETS = {
    'loc_dinh_ky': {
        'pitch_shift_semitones': 3.8,
        'formant_center_hz': 2400.0,
        'formant_boost_db': 4.5,
        'morph_strength': 0.90
    },
    'tay_du_ky': {
        'pitch_shift_semitones': 4.6,
        'formant_center_hz': 2800.0,
        'formant_boost_db': 5.0,
        'morph_strength': 0.92
    },
    'storytelling': {
        'pitch_shift_semitones': 0.5,
        'formant_center_hz': 1800.0,
        'formant_boost_db': 2.5,
        'morph_strength': 0.70
    },
    'serious': {
        'pitch_shift_semitones': -2.8,
        'formant_center_hz': 650.0,
        'formant_boost_db': 3.5,
        'morph_strength': 0.85
    },
    'lali5': {
        'pitch_shift_semitones': 3.5,
        'formant_center_hz': 2300.0,
        'formant_boost_db': 4.0,
        'morph_strength': 0.88
    },
    'neutral': {
        'pitch_shift_semitones': 0.0,
        'formant_center_hz': 1750.0,
        'formant_boost_db': 0.0,
        'morph_strength': 0.0
    }
}

class FourierSpectralEngine:
    _instance = None

    def __init__(self, n_fft=2048, hop_length=512, win_length=2048):
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.target_sr = 24000
        self.cached_envelopes = {}

    def get_style_spectral_envelope(self, style_id):
        clean_sid = style_id.lower().strip()
        if clean_sid in self.cached_envelopes:
            return self.cached_envelopes[clean_sid]

        ref_candidates = [
            os.path.join(PROJECT_ROOT, 'data', 'voice', clean_sid, 'reference.wav'),
            os.path.join(PROJECT_ROOT, 'data', 'raw', clean_sid, 'reference.wav')
        ]
        
        style_voice_dir = os.path.join(PROJECT_ROOT, 'data', 'voice', clean_sid)
        if os.path.exists(style_voice_dir):
            for ext in ('*.wav', '*.mp3', '*.m4a'):
                ref_candidates.extend(glob.glob(os.path.join(style_voice_dir, ext)))

        target_file = None
        for cand in ref_candidates:
            if os.path.exists(cand) and os.path.getsize(cand) > 1000:
                target_file = cand
                break

        if target_file:
            try:
                try:
                    audio, sr = sf.read(target_file)
                except Exception:
                    import librosa
                    audio, sr = librosa.load(target_file, sr=self.target_sr)

                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)

                if sr != self.target_sr:
                    num_samples = int(len(audio) * float(self.target_sr) / sr)
                    audio = scipy.signal.resample(audio, num_samples)

                f, t, Zxx = scipy.signal.stft(
                    audio,
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
                self.cached_envelopes[clean_sid] = norm_env
                return norm_env
            except Exception as e:
                print(f'Error extracting envelope for {clean_sid}: {e}')

        preset = CHARACTER_PRESETS.get(clean_sid, CHARACTER_PRESETS['neutral'])
        center = preset.get('formant_center_hz', 2000.0)
        freqs = np.linspace(0, self.target_sr / 2, self.n_fft // 2 + 1)
        synthetic_env = 1.0 + 1.5 * np.exp(-0.5 * ((freqs - center) / 600.0) ** 2)
        synthetic_env /= np.mean(synthetic_env)
        self.cached_envelopes[clean_sid] = synthetic_env
        return synthetic_env

    def apply_voice_morphing(self, audio_float, style_id, sr=24000):
        clean_sid = style_id.lower().strip() if style_id else 'neutral'
        preset = CHARACTER_PRESETS.get(clean_sid, {})
        
        pitch_shift = preset.get('pitch_shift_semitones', 0.0)
        formant_center = preset.get('formant_center_hz', 2200.0)
        formant_boost_db = preset.get('formant_boost_db', 3.5)
        morph_strength = preset.get('morph_strength', 0.85)

        out_audio = audio_float.copy()
        if abs(pitch_shift) > 0.1:
            try:
                import librosa
                out_audio = librosa.effects.pitch_shift(out_audio, sr=sr, n_steps=pitch_shift)
            except Exception as e:
                print(f'Pitch shift notice: {e}')

        if clean_sid == 'neutral' and abs(pitch_shift) < 0.1:
            return out_audio

        try:
            target_env = self.get_style_spectral_envelope(clean_sid)

            f, t, Zxx = scipy.signal.stft(
                out_audio,
                fs=sr,
                window='hann',
                nperseg=self.win_length,
                noverlap=self.win_length - self.hop_length,
                nfft=self.n_fft
            )
            mag = np.abs(Zxx)
            phase = np.angle(Zxx)

            src_env = scipy.ndimage.gaussian_filter1d(mag, sigma=4.0, axis=0)
            src_env = np.maximum(src_env, 1e-6)

            target_env_2d = target_env[:, np.newaxis]
            src_mean = np.mean(src_env, axis=0, keepdims=True)
            src_norm_env = src_env / np.maximum(src_mean, 1e-6)

            ratio = target_env_2d / np.maximum(src_norm_env, 1e-6)
            ratio = np.clip(ratio, 0.3, 3.5)

            transfer_gain = 1.0 + morph_strength * (ratio - 1.0)

            freq_bins = f
            formant_mask = (freq_bins >= (formant_center - 800)) & (freq_bins <= (formant_center + 1200))
            boost_linear = 10.0 ** (formant_boost_db / 20.0)
            transfer_gain[formant_mask, :] *= (1.0 + 0.6 * (boost_linear - 1.0))

            mag_modified = mag * transfer_gain
            Zxx_modified = mag_modified * np.exp(1j * phase)

            _, y_out = scipy.signal.istft(
                Zxx_modified,
                fs=sr,
                window='hann',
                nperseg=self.win_length,
                noverlap=self.win_length - self.hop_length,
                nfft=self.n_fft
            )

            if len(y_out) != len(audio_float):
                if len(y_out) > len(audio_float):
                    y_out = y_out[:len(audio_float)]
                else:
                    y_out = np.pad(y_out, (0, len(audio_float) - len(y_out)))

            max_val = np.max(np.abs(y_out))
            if max_val > 1e-6:
                y_out = y_out / max_val * 0.94

            return y_out.astype(np.float32)

        except Exception as e:
            print(f'Fourier Morphing error: {e}')
            return out_audio

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FourierSpectralEngine()
        return cls._instance
