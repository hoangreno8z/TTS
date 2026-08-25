"""Unit tests for Phase 8 & Custom Style Profile Manager (including lali5)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.style_manager import StyleManager, StyleProfile

class TestStyleManager(unittest.TestCase):
    def setUp(self):
        self.mgr = StyleManager()

    def test_01_list_default_styles(self):
        """Ensure all 3 default styles exist."""
        styles = self.mgr.list_styles()
        self.assertGreaterEqual(len(styles), 3)
        style_ids = [s["style_id"] for s in styles]
        self.assertIn("neutral", style_ids)
        self.assertIn("serious", style_ids)
        self.assertIn("storytelling", style_ids)

    def test_02_add_and_persist_custom_style_lali5(self):
        """Test adding and saving a custom character voice style 'lali5'."""
        prof = self.mgr.add_custom_style(
            style_id="lali5",
            name="Style Lali5 (Nhân vật Lali 5)",
            description="Phong cách giọng nhân vật Lali5 năng động, đáng yêu",
            speed=1.08,
            pause_multiplier=0.95,
            pitch_adjustment=0.5
        )
        self.assertEqual(prof.style_id, "lali5")
        self.assertEqual(prof.speed, 1.08)

        # Check retrieval
        retrieved = self.mgr.get_style("lali5")
        self.assertEqual(retrieved.style_id, "lali5")
        self.assertEqual(retrieved.name, "Style Lali5 (Nhân vật Lali 5)")

        # Verify folder creation
        raw_folder = os.path.join(self.mgr.project_root, "data", "raw", "lali5")
        voice_folder = os.path.join(self.mgr.project_root, "data", "voice", "lali5")
        self.assertTrue(os.path.exists(raw_folder))
        self.assertTrue(os.path.exists(voice_folder))

    def test_03_unknown_style_fallback(self):
        st = self.mgr.get_style("random_nonexistent_style_123")
        self.assertEqual(st.style_id, "neutral")

if __name__ == "__main__":
    unittest.main()
