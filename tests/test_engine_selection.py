"""Unit tests for Phase 7 Engine Selection and EngineFactory."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.engine_factory import EngineFactory
from app.adapters.f5_tts_adapter import F5TTSAdapter
from app.adapters.gpt_sovits_adapter import GPTSoVITSAdapter

class TestEngineSelection(unittest.TestCase):
    def test_01_load_config(self):
        cfg = EngineFactory.load_config()
        self.assertIn("engines", cfg)
        self.assertEqual(cfg["engines"]["selected_engine"], "f5-tts")
        self.assertEqual(cfg["engines"]["fallback_engine"], "gpt-sovits")

    def test_02_default_selected_adapter(self):
        adapter = EngineFactory.get_engine_adapter()
        self.assertIsInstance(adapter, F5TTSAdapter)
        self.assertEqual(adapter.engine_name, "f5-tts")

    def test_03_override_engine_adapter(self):
        adapter = EngineFactory.get_engine_adapter(engine_name="gpt-sovits")
        self.assertIsInstance(adapter, GPTSoVITSAdapter)
        self.assertEqual(adapter.engine_name, "gpt-sovits")

    def test_04_invalid_engine_name(self):
        with self.assertRaises(ValueError):
            EngineFactory.get_engine_adapter(engine_name="non_existent_engine")

if __name__ == "__main__":
    unittest.main()
