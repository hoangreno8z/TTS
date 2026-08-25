"""Unit tests for GPT-SoVITS Adapter (Phase 5)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.adapters.base_adapter import BaseTTSAdapter
from app.adapters.f5_tts_adapter import F5TTSAdapter
from app.adapters.gpt_sovits_adapter import GPTSoVITSAdapter

class TestGPTSoVITSAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = GPTSoVITSAdapter()

    def test_01_interface_inheritance(self):
        """Ensure GPTSoVITSAdapter properly subclasses BaseTTSAdapter."""
        self.assertIsInstance(self.adapter, BaseTTSAdapter)
        self.assertEqual(self.adapter.engine_name, "gpt-sovits")

    def test_02_model_info_and_license(self):
        """Ensure model metadata and license distinctions are preserved."""
        info = self.adapter.get_model_info()
        self.assertEqual(info["code_license"], "MIT")
        self.assertIn("upstream_repo", info)
        self.assertIn("GPT-SoVITS", info["upstream_repo"])

    def test_03_is_available_status(self):
        """Status check should return boolean without throwing unhandled exceptions."""
        avail = self.adapter.is_available()
        self.assertIsInstance(avail, bool)

    def test_04_adapter_isolation(self):
        """Ensure F5-TTS and GPT-SoVITS adapters do not interfere with each other."""
        f5 = F5TTSAdapter()
        sovits = GPTSoVITSAdapter()
        self.assertNotEqual(f5.engine_name, sovits.engine_name)
        self.assertEqual(f5.get_model_info()["code_license"], "MIT")
        self.assertEqual(sovits.get_model_info()["code_license"], "MIT")

if __name__ == "__main__":
    unittest.main()
