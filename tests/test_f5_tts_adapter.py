"""Unit tests for F5-TTS Adapter (Phase 4)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.adapters.base_adapter import BaseTTSAdapter
from app.adapters.f5_tts_adapter import F5TTSAdapter

class TestF5TTSAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = F5TTSAdapter()

    def test_01_interface_inheritance(self):
        """Ensure F5TTSAdapter properly subclasses BaseTTSAdapter."""
        self.assertIsInstance(self.adapter, BaseTTSAdapter)
        self.assertEqual(self.adapter.engine_name, "f5-tts")

    def test_02_model_info_and_license(self):
        """Ensure model metadata and license distinctions are preserved."""
        info = self.adapter.get_model_info()
        self.assertEqual(info["code_license"], "MIT")
        self.assertIn("CC-BY-NC", info["model_license"])
        self.assertIn("upstream_repo", info)
        self.assertIn("vietnamese_reference", info)

    def test_03_is_available_status(self):
        """Status check should return boolean without throwing unhandled exceptions."""
        avail = self.adapter.is_available()
        self.assertIsInstance(avail, bool)

if __name__ == "__main__":
    unittest.main()
