"""Base TTS Adapter Interface contract as defined in docs/02_ARCHITECTURE.md.
All TTS engines (F5-TTS, GPT-SoVITS, etc.) must implement this common interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTTSAdapter(ABC):
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.is_loaded = False
        self.model = None

    @abstractmethod
    def is_available(self) -> bool:
        """Check if required upstream dependencies and models are installed/accessible."""
        pass

    @abstractmethod
    def load_model(self, checkpoint_path: Optional[str] = None, **kwargs) -> bool:
        """Load model weights into memory (CPU/GPU)."""
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = "",
        style_profile: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synthesize text using the reference audio and style.
        Returns:
            wav_path (str): Path to generated WAV file.
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return engine metadata, licenses, and current status."""
        pass
