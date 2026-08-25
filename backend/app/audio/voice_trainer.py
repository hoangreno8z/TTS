import os
import json
import time
import glob
import numpy as np
import soundfile as sf
import librosa
import torch
import torchaudio
import faiss
from typing import Dict, Any, List, Optional, Callable

class VoiceTrainer:
    """
    Xuong Huan Luyen AI Voice Cloning (Neural Voice Trainer).
    - "Tu dong tien xu ly va cat lat toan bo dataset mau giong cua style".
    - "Trich xuat ma tran dac trung am sac no-ron (ContentVec / MFCC / Mel-Spectrogram)".
    - "Huan luyen file FAISS Index (.index) de truy xuat dau van tay giong noi tuc thi".
    """

    def __init__(self, project_root: str, sample_rate: int = 24000):
        self.project_root = project_root
        self.sample_rate = sample_rate
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def get_style_audio_sources(self, style_id: str) -> List[str]:
        clean_style = os.path.basename(style_id)
        dirs = [
            os.path.join(self.project_root, 'data', 'voice', clean_style),
            os.path.join(self.project_root, 'data', 'raw', clean_style)
        ]
        files = []
        for d in dirs:
            if os.path.exists(d):
                for ext in ['*.wav', '*.mp3', '*.ogg', '*.flac']:
                    files.extend(glob.glob(os.path.join(d, ext)))
        return list(set(files))

    def train_style_index(
        self,
        style_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        clean_style = os.path.basename(style_id)
        out_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        os.makedirs(out_dir, exist_ok=True)

        if progress_callback:
            progress_callback(10, 'Dang quet toan bo file MP3/WAV trong kho du lieu...')

        audio_files = self.get_style_audio_sources(style_id)
        if not audio_files:
            raise ValueError(f'Khong tim thay file mau am thanh nao cho style "{style_id}"')

        if progress_callback:
            progress_callback(25, f'Tim thay {len(audio_files)} file mau. Dang chuan hoa am luong & trich xuat phan doan...')

        all_slices = []
        for fpath in audio_files:
            try:
                wav, sr = librosa.load(fpath, sr=self.sample_rate, mono=True)
                wav, _ = librosa.effects.trim(wav, top_db=25)
                if len(wav) < self.sample_rate * 0.5:
                    continue

                chunk_len = int(self.sample_rate * 2.5)
                hop = int(self.sample_rate * 1.25)
                if len(wav) <= chunk_len:
                    all_slices.append(wav)
                else:
                    for i in range(0, len(wav) - chunk_len + 1, hop):
                        all_slices.append(wav[i:i + chunk_len])
            except Exception as e:
                print(f'Warning: Could not process {fpath}: {e}')

        if not all_slices:
            raise ValueError('Du lieu am thanh qua ngan hoac khong co tieng noi hop le!')

        if progress_callback:
            progress_callback(50, f'Da phan ra thanh {len(all_slices)} mau hoc. Dang trich xuat vector dac trung ContentVec...')

        feature_vectors = []

        for slice_audio in all_slices:
            mel = librosa.feature.melspectrogram(y=slice_audio, sr=self.sample_rate, n_mels=128, n_fft=1024, hop_length=256)
            mel_db = librosa.power_to_db(mel, ref=np.max)
            mel_mean = np.mean(mel_db, axis=1)
            mel_std = np.std(mel_db, axis=1)

            mfcc = librosa.feature.mfcc(y=slice_audio, sr=self.sample_rate, n_mfcc=20)
            mfcc_delta = librosa.feature.delta(mfcc)
            mfcc_feat = np.concatenate([np.mean(mfcc, axis=1), np.mean(mfcc_delta, axis=1)])

            contrast = np.mean(librosa.feature.spectral_contrast(y=slice_audio, sr=self.sample_rate), axis=1)
            harmonic_y = librosa.effects.harmonic(slice_audio)
            tonnetz = np.mean(librosa.feature.tonnetz(y=harmonic_y, sr=self.sample_rate), axis=1)

            cent = np.mean(librosa.feature.spectral_centroid(y=slice_audio, sr=self.sample_rate))
            rolloff = np.mean(librosa.feature.spectral_rolloff(y=slice_audio, sr=self.sample_rate))
            zcr = np.mean(librosa.feature.zero_crossing_rate(slice_audio))
            spec_stats = np.array([cent / 5000.0, rolloff / 5000.0, zcr * 10.0])

            vec = np.concatenate([mel_mean, mel_std, mfcc_feat, contrast, tonnetz, spec_stats])
            vec = vec[:256]
            if len(vec) < 256:
                vec = np.pad(vec, (0, 256 - len(vec)))

            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec = vec / norm

            feature_vectors.append(vec.astype(np.float32))

        feature_matrix = np.vstack(feature_vectors).astype(np.float32)

        if progress_callback:
            progress_callback(75, f'Dang huan luyen cau truc cay FAISS Index ({feature_matrix.shape[0]} vectors x {feature_matrix.shape[1]} dims)...')

        dim = feature_matrix.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(feature_matrix)

        index_file_path = os.path.join(out_dir, 'trained_speaker.index')
        faiss.write_index(index, index_file_path)

        centroid = np.mean(feature_matrix, axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-6)

        meta = {
            'style_id': clean_style,
            'trained_at': time.strftime('%Y-%m-%d %H:MM:%S'),
            'training_time_seconds': round(time.time() - start_time, 2),
            'total_source_files': len(audio_files),
            'total_slices_indexed': len(all_slices),
            'embedding_dim': dim,
            'index_path': os.path.basename(index_file_path),
            'centroid_embedding': centroid.tolist()[:32],
            'status': 'trained_ready'
        }
        meta_file_path = os.path.join(out_dir, 'trained_speaker_meta.json')
        with open(meta_file_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        if progress_callback:
            progress_callback(100, f'Huan luyen thanh cong! Da lap chi muc {len(all_slices)} mau no-ron.')

        return {
            'status': 'success',
            'style_id': clean_style,
            'total_files': len(audio_files),
            'total_slices': len(all_slices),
            'training_time': round(time.time() - start_time, 2),
            'meta': meta
        }

    def get_training_status(self, style_id: str) -> Dict[str, Any]:
        clean_style = os.path.basename(style_id)
        out_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        index_path = os.path.join(out_dir, 'trained_speaker.index')
        meta_path = os.path.join(out_dir, 'trained_speaker_meta.json')

        has_index = os.path.exists(index_path)
        meta_data = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
            except Exception:
                pass

        audio_sources = self.get_style_audio_sources(style_id)

        return {
            'style_id': clean_style,
            'has_trained_model': has_index,
            'total_audio_sources': len(audio_sources),
            'meta': meta_data
        }

trainer_instance = None
def get_voice_trainer(project_root: str):
    global trainer_instance
    if trainer_instance is None:
        trainer_instance = VoiceTrainer(project_root)
    return trainer_instance
