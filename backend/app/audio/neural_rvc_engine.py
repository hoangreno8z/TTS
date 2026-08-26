import os
import sys
import time
import numpy as np
import soundfile as sf
import torch

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "models")):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", ".."))

RVC_DIR = os.path.join(curr_dir, "Retrieval-based-Voice-Conversion-WebUI-main")

class NeuralRVCEngine:
    _instance = None

    def __init__(self):
        self.vc = None
        self.loaded_model = None
        self.init_engine()

    def init_engine(self):
        try:
            if not os.path.exists(RVC_DIR):
                return
            
            os.environ["weight_root"] = os.path.join(RVC_DIR, "assets", "weights")
            os.environ["index_root"] = os.path.join(PROJECT_ROOT, "models", "rvc")
            os.environ["outside_index_root"] = os.path.join(PROJECT_ROOT, "models", "rvc")
            os.environ["rmvpe_root"] = os.path.join(RVC_DIR, "assets", "rmvpe")

            if RVC_DIR not in sys.path:
                sys.path.insert(0, RVC_DIR)

            old_cwd = os.getcwd()
            os.chdir(RVC_DIR)
            from configs.config import Config
            from infer.vc.modules import VC

            config = Config()
            config.device = "cpu"
            config.is_half = False
            self.vc = VC(config)
            os.chdir(old_cwd)
        except Exception as e:
            print(f"NeuralRVCEngine init notice: {e}")

    def convert(self, input_wav_path: str, output_wav_path: str, style_id: str = "loc_dinh_ky", f0_up_key: int = 4) -> bool:
        if self.vc is None:
            return False

        clean_sid = style_id.lower().strip().replace(" ", "_")
        weight_file = f"{clean_sid}.pth"
        
        weight_path = os.path.join(RVC_DIR, "assets", "weights", weight_file)
        if not os.path.exists(weight_path):
            alt_path = os.path.join(PROJECT_ROOT, "models", "rvc", "loc-dinh-ky_60e_6120s.pth")
            if os.path.exists(alt_path):
                import shutil
                os.makedirs(os.path.dirname(weight_path), exist_ok=True)
                shutil.copyfile(alt_path, weight_path)

        if not os.path.exists(weight_path):
            return False

        index_file = os.path.join(PROJECT_ROOT, "models", "rvc", f"{clean_sid}.index")
        if not os.path.exists(index_file):
            index_file = ""

        try:
            old_cwd = os.getcwd()
            os.chdir(RVC_DIR)
            
            if self.loaded_model != weight_file:
                self.vc.get_vc(weight_file)
                self.loaded_model = weight_file

            msg, out_audio = self.vc.vc_single(
                sid=0,
                input_audio_path=input_wav_path,
                f0_up_key=int(f0_up_key),
                f0_method="pm",
                file_index=index_file,
                index_rate=0.95,
                resample_sr=0,
                rms_mix_rate=0.1,
                protect=0.33
            )
            os.chdir(old_cwd)

            if out_audio is not None:
                sr, data = out_audio
                sf.write(output_wav_path, data, sr)
                return True
            return False
        except Exception as e:
            print(f"Neural RVC conversion error: {e}")
            return False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = NeuralRVCEngine()
        return cls._instance
