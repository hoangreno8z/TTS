"""Unit tests for Phase 6 Benchmark Comparison and Blind Evaluation Packager."""
import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from compare_results import build_blind_test_kit, compile_comparison_report

class TestCompareBenchmark(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_01_build_blind_test_kit(self):
        """Test blind test key mapping creation."""
        key_map = build_blind_test_kit(self.project_root, seed=123)
        self.assertEqual(len(key_map), 20)
        for s_id in range(1, 21):
            key = f"sentence_{s_id:02d}"
            self.assertIn(key, key_map)
            self.assertIn(key_map[key]["sample_A"], ["f5-tts", "gpt-sovits"])
            self.assertIn(key_map[key]["sample_B"], ["f5-tts", "gpt-sovits"])
            self.assertNotEqual(key_map[key]["sample_A"], key_map[key]["sample_B"])

    def test_02_compile_comparison_report(self):
        """Test report and results.json generation."""
        compile_comparison_report(self.project_root)
        results_json = os.path.join(self.project_root, "benchmark", "results.json")
        report_md = os.path.join(self.project_root, "benchmark", "report.md")

        self.assertTrue(os.path.exists(results_json))
        self.assertTrue(os.path.exists(report_md))

        with open(results_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["total_benchmark_sentences"], 20)
            self.assertIn("f5-tts", data["engines_compared"])
            self.assertIn("gpt-sovits", data["engines_compared"])

if __name__ == "__main__":
    unittest.main()
