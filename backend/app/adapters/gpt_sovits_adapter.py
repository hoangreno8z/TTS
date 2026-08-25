"""GPT-SoVITS Adapter Implementation.
Wraps upstream GPT-SoVITS (Few-shot/Zero-shot TTS, MIT License)
behind the standard BaseTTSAdapter interface without mixing engine internals.
"""
import os
import sys
import time
from typing import Dict, Any, Optional

from .base_adapter import BaseTTSAdapter
from ..text_norm import VietnameseNormalizer
from ..audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

class GPTSoVITSAdapter(BaseTTSAdapter):
    def __init__(
        self,
        gpt_path: Optional[str] = None,
        sovits_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        super().__init__(engine_name="gpt-sovits")
        self.gpt_path = gpt_path
        self.sovits_path = sovits_path
        self.device = device or ("cuda" if self._check_cuda() else "cpu")
        self.model_info = {
            "name": "GPT-SoVITS (Few-shot Voice Conversion & TTS)",
            "upstream_repo": "https://github.com/RVC-Boss/GPT-SoVITS",
            "code_license": "MIT",
            "model_license": "Release/Checkpoint Specific (V1/V2)",
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
        """Check if GPT-SoVITS inference modules and PyTorch are present."""
        try:
            import torch
            # Check for GPT-SoVITS package or CLI/API vendor
            import GPT_SoVITS
            return True
        except ImportError:
            return False

    def load_model(
        self,
        checkpoint_path: Optional[str] = None,
        gpt_path: Optional[str] = None,
        sovits_path: Optional[str] = None,
        **kwargs
    ) -> bool:
        if gpt_path:
            self.gpt_path = gpt_path
        if sovits_path:
            self.sovits_path = sovits_path
        if checkpoint_path and not self.sovits_path:
            self.sovits_path = checkpoint_path

        if not self.is_available():
            print("GPT-SoVITS or PyTorch is not installed in the current local environment.")
            return False

        try:
            # Dynamic import when available
            from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights
            if self.gpt_path:
                change_gpt_weights(self.gpt_path)
            if self.sovits_path:
                change_sovits_weights(self.sovits_path)
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Failed to load GPT-SoVITS weights: {e}")
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
        """Synthesize speech using GPT-SoVITS adapter.
        1. Normalizes Vietnamese text.
        2. Normalizes reference audio if needed.
        3. Executes inference via GPT-SoVITS API.
        4. Saves and returns output wav path.
        """
        options = options or {}
        output_dir = options.get("output_dir", os.path.join(".", "outputs", "gpt_sovits"))
        os.makedirs(output_dir, exist_ok=True)

        norm_text = VietnameseNormalizer.normalize(text)
        norm_ref_text = VietnameseNormalizer.normalize(reference_text) if reference_text else ""

        speed = options.get("speed", 1.0)
        if style_profile and "speed" in style_profile:
            speed = style_profile["speed"]

        timestamp = int(time.time() * 1000)
        out_filename = f"sovits_gen_{timestamp}.wav"
        out_wav_path = os.path.join(output_dir, out_filename)

        if not self.is_available():
            raise RuntimeError(
                "GPT-SoVITS upstream dependency is not available in local environment. "
                "Please run inference via Google Colab Free Tier script (notebooks/02_gpt_sovits_colab_benchmark.py) "
                "or install torch & GPT-SoVITS."
            )

        # Real inference with GPT-SoVITS
        from GPT_SoVITS.inference_webui import get_tts_wav
        
        # Call GPT-SoVITS synthesis pipeline
        gen = get_tts_wav(
            ref_wav_path=reference_audio,
            prompt_text=norm_ref_text,
            prompt_language="vi",
            text=norm_text,
            text_language="vi",
            how_to_cut="凑四句一切",
            speed=speed
        )
        
        # Extract audio output
        sr, audio_data = next(gen)
        import soundfile as sf
        sf.write(out_wav_path, audio_data, sr)
        return out_wav_path

    def get_model_info(self) -> Dict[str, Any]:
        info = dict(self.model_info)
        info["is_loaded"] = self.is_loaded
        info["gpt_path"] = self.gpt_path
        info["sovits_path"] = self.sovits_path
        return info
