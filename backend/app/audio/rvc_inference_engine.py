"""Real RVC v2 Neural Voice Conversion Inference Engine.
Loads trained weights (.pth) and Faiss index (.index) to convert speech into target voice identity
using the official RVC v2 neural VITS generator on local CPU.
"""
import os
import sys
import numpy as np
import scipy.signal
import soundfile as sf
import torch

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "models")):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "rvc")
RVC_ROOT = os.path.join(curr_dir, "Retrieval-based-Voice-Conversion-WebUI-main")

class RVCInferenceEngine:
    _instance = None

    def __init__(self, model_filename: str = "loc-dinh-ky_60e_6120s.pth", index_filename: str = "loc-dinh-ky.index"):
        self.model_path = os.path.join(MODELS_DIR, model_filename)
        self.index_path = os.path.join(MODELS_DIR, index_filename)
        self.target_sr = 40000
        self.is_loaded = False
        self.vc = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            print(f"RVC Notice: Model file not found at {self.model_path}")
            return

        try:
            old_cwd = os.getcwd()
            os.chdir(RVC_ROOT)
            if RVC_ROOT not in sys.path:
                sys.path.insert(0, RVC_ROOT)
            os.environ["weight_root"] = os.path.join(RVC_ROOT, "assets", "weights")
            os.environ["index_root"] = os.path.join(RVC_ROOT, "logs")
            os.environ["rmvpe_root"] = os.path.join(RVC_ROOT, "assets", "rmvpe")
            os.environ["hubert_path"] = os.path.join(RVC_ROOT, "assets", "hubert", "hubert_base.pt")

            from infer.vc.modules import VC
            from configs.config import Config
            config = Config()
            config.device = "cpu"
            config.is_half = False
            self.vc = VC(config)
            
            tgt_pth = os.path.join(RVC_ROOT, "assets", "weights", "loc_dinh_ky.pth")
            os.makedirs(os.path.dirname(tgt_pth), exist_ok=True)
            if not os.path.exists(tgt_pth):
                import shutil
                shutil.copyfile(self.model_path, tgt_pth)

            self.vc.get_vc("loc_dinh_ky.pth")
            self.target_sr = self.vc.tgt_sr or 40000
            self.is_loaded = True
            print(f"-> RVC v2 Neural Model Loaded Successfully on CPU! (SR: {self.target_sr}Hz)")
            os.chdir(old_cwd)
        except Exception as e:
            print(f"-> Error loading RVC model: {e}")
            os.chdir(PROJECT_ROOT)

    def convert_voice(
        self,
        audio_float: np.ndarray,
        source_sr: int = 24000,
        pitch_shift_semitones: float = 0.0,
        index_rate: float = 0.75
    ) -> np.ndarray:
        """Convert input speech audio into target trained voice using local neural RVC."""
        if not self.is_loaded or self.vc is None:
            return audio_float

        try:
            temp_in = os.path.join(PROJECT_ROOT, "outputs", "temp_rvc_in.wav")
            os.makedirs(os.path.dirname(temp_in), exist_ok=True)
            sf.write(temp_in, audio_float, source_sr)

            old_cwd = os.getcwd()
            os.chdir(RVC_ROOT)
            os.environ["rmvpe_root"] = os.path.join(RVC_ROOT, "assets", "rmvpe")

            index_file = self.index_path if os.path.exists(self.index_path) else ""
            info, opt = self.vc.vc_single(
                0,
                temp_in,
                int(pitch_shift_semitones),
                "rmvpe",
                index_file,
                float(index_rate),
                3,
                0,
                0.55
            )
            os.chdir(old_cwd)

            if os.path.exists(temp_in):
                try:
                    os.remove(temp_in)
                except OSError:
                    pass

            if opt is not None:
                out_sr, out_data = opt
                if out_sr != source_sr:
                    num_samples = int(len(out_data) * float(source_sr) / out_sr)
                    out_data = scipy.signal.resample(out_data, num_samples)
                return out_data.astype(np.float32)
            return audio_float

        except Exception as e:
            print(f"RVC conversion fallback: {e}")
            return audio_float

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RVCInferenceEngine()
        return cls._instance
