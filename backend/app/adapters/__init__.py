"""TTS Adapters package for LAPQUE Personal Vietnamese TTS."""
from .base_adapter import BaseTTSAdapter
from .f5_tts_adapter import F5TTSAdapter
from .gpt_sovits_adapter import GPTSoVITSAdapter

__all__ = ["BaseTTSAdapter", "F5TTSAdapter", "GPTSoVITSAdapter"]
