"""Unit tests for LAPQUE V7 Dual-Core Architecture (Parametric Core 0-AI vs Local Neural Core)."""
import unittest
import numpy as np
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from app.audio.world_parametric_core import WorldParametricCore
from app.audio.neural_vc_core import NeuralVCCore
from app.main import app
from fastapi.testclient import TestClient

class TestV7DualCore(unittest.TestCase):
    def setUp(self):
        self.sr = 24000
        # Synthetic harmonic signal simulating vocal tract
        t = np.linspace(0, 0.5, int(0.5 * self.sr))
        self.synth_audio = (
            0.6 * np.sin(2 * np.pi * 150 * t) +
            0.3 * np.sin(2 * np.pi * 300 * t) +
            0.1 * np.sin(2 * np.pi * 600 * t)
        ).astype(np.float64)
        self.client = TestClient(app)

    def test_world_parametric_core_reconstruction_g1(self):
        core = WorldParametricCore(sample_rate=self.sr)
        metrics = core.test_reconstruction_g1(self.synth_audio)
        self.assertIn("g1_mcd_db", metrics)
        self.assertIn("g1_f0_rmse_hz", metrics)
        self.assertIn("g1_passed", metrics)

    def test_world_parametric_core_mcep_vtln(self):
        core = WorldParametricCore(sample_rate=self.sr)
        f0, sp, ap = core.analyze(self.synth_audio)
        mcep = core.sp_to_mcep(sp, num_coeffs=24)
        self.assertEqual(mcep.shape[1], 24)

        warped_sp = core.apply_vtln_warping(sp, warp_alpha=0.88)
        self.assertEqual(warped_sp.shape, sp.shape)

        out_wav = core.transform_style(self.synth_audio, pitch_shift_semitones=3.0, vtln_alpha=0.88)
        self.assertGreater(len(out_wav), 0)
        self.assertLessEqual(np.max(np.abs(out_wav)), 1.0)

    def test_neural_vc_core_timbre_transfer(self):
        core = NeuralVCCore(sample_rate=self.sr)
        ref_audio = self.synth_audio.astype(np.float32)
        emb = core.extract_speaker_embedding(ref_audio)
        self.assertIn("timbre_vector", emb)
        self.assertIn("peak_mel_band", emb)
        self.assertEqual(len(emb["timbre_vector"]), 160) # 80 mean + 80 std

        out_wav = core.convert_voice(ref_audio, speaker_embedding=emb, pitch_shift_semitones=3.66)
        self.assertEqual(len(out_wav), len(ref_audio))
        self.assertLessEqual(np.max(np.abs(out_wav)), 1.0)

    def test_api_synthesis_parametric_mode(self):
        res = self.client.post("/tts", json={
            "text": "Kiểm tra kiến trúc V7 Core 1 Parametric 0-AI.",
            "style_id": "loc_dinh_ky",
            "core_mode": "parametric"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("audio_file", data)

    def test_api_synthesis_neural_mode(self):
        res = self.client.post("/tts", json={
            "text": "Kiểm tra kiến trúc V7 Core 2 Local Neural AI.",
            "style_id": "loc_dinh_ky",
            "core_mode": "neural"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("audio_file", data)

if __name__ == "__main__":
    unittest.main()
