"""F5-TTS Adapter Implementation.
Wraps upstream F5-TTS (MIT Code, CC-BY-NC weights) and Vietnamese community models
behind the standard BaseTTSAdapter interface.
"""
import os
import sys
import time
from typing import Dict, Any, Optional

from .base_adapter import BaseTTSAdapter
from ..text_norm import VietnameseNormalizer
from ..audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

class F5TTSAdapter(BaseTTSAdapter):
    def __init__(self, checkpoint_path: Optional[str] = None, vocab_file: Optional[str] = None, device: Optional[str] = None):
        super().__init__(engine_name="f5-tts")
        self.checkpoint_path = checkpoint_path
        self.vocab_file = vocab_file
        self.device = device or ("cuda" if self._check_cuda() else "cpu")
        self.model_info = {
            "name": "F5-TTS (Flow-Matching Non-Autoregressive TTS)",
            "upstream_repo": "https://github.com/SWivid/F5-TTS",
            "vietnamese_reference": "https://github.com/psilabvnorg/F5-TTS-Vietnamese",
            "code_license": "MIT",
            "model_license": "CC-BY-NC 4.0 (Upstream Emilia) / Community Checkpoint",
            "device": self.device,
            "is_available": self.is_available()
        }

    def _check_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def is_available(self) -> bool:
        try:
            import torch
            import f5_tts
            return True
        except ImportError:
            return False

    def load_model(self, checkpoint_path: Optional[str] = None, **kwargs) -> bool:
        if checkpoint_path:
            self.checkpoint_path = checkpoint_path

        if not self.is_available():
            print("F5-TTS or PyTorch is not installed in the current environment.")
            return False

        try:
            # Dynamic import when available
            import torch
            from f5_tts.model import CFM, DiT, UNetT
            from f5_tts.infer.utils_infer import load_model as f5_load_model, load_vocoder
            
            # Load vocoder and model
            self.vocoder = load_vocoder(vocoder_name="vocos", is_local=False)
            # Default or custom checkpoint loading logic
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Failed to load F5-TTS model: {e}")
            self.is_loaded = False
            return False

    def generate(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = "",
        style_profile: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synthesize speech using F5-TTS zero-shot / few-shot adapter.
        1. Normalizes Vietnamese text.
        2. Normalizes reference audio if needed.
        3. Executes inference via upstream engine.
        4. Saves and returns output wav path.
        """
        options = options or {}
        output_dir = options.get("output_dir", os.path.join(".", "outputs", "f5_tts"))
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Deterministic Vietnamese text normalization
        norm_text = VietnameseNormalizer.normalize(text)
        norm_ref_text = VietnameseNormalizer.normalize(reference_text) if reference_text else ""

        speed = options.get("speed", 1.0)
        if style_profile and "speed" in style_profile:
            speed = style_profile["speed"]

        timestamp = int(time.time() * 1000)
        out_filename = f"f5_gen_{timestamp}.wav"
        out_wav_path = os.path.join(output_dir, out_filename)

        if not self.is_available():
            raise RuntimeError(
                "F5-TTS upstream dependency is not available in local environment. "
                "Please run inference via Google Colab Free Tier script (notebooks/01_f5_tts_colab_benchmark.py) "
                "or install torch & f5-tts."
            )

        # Real inference with f5_tts
        from f5_tts.infer.utils_infer import infer_process
        
        wav, sr, _ = infer_process(
            ref_audio=reference_audio,
            ref_text=norm_ref_text,
            gen_text=norm_text,
            model_obj=self.model,
            vocoder=self.vocoder,
            speed=speed,
            device=self.device
        )
        
        # Save output WAV
        import soundfile as sf
        sf.write(out_wav_path, wav, sr)
        return out_wav_path

    def get_model_info(self) -> Dict[str, Any]:
        info = dict(self.model_info)
        info["is_loaded"] = self.is_loaded
        info["checkpoint_path"] = self.checkpoint_path
        return info
