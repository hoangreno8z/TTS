"""Integration and Unit Tests for FastAPI Endpoints (Phase 11)."""
import os
import sys
import unittest
import io
import math

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.main import app, OUTPUTS_DIR
from app.audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

client = TestClient(app)

class TestAPIEndpoints(unittest.TestCase):
    def test_01_health_endpoint(self):
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["service"], "lapque-tts")
        self.assertEqual(data["max_characters"], 5000)
        self.assertIn("selected_engine", data)

    def test_02_styles_endpoint(self):
        resp = client.get("/styles")
        self.assertEqual(resp.status_code, 200)
        styles = resp.json()
        self.assertGreaterEqual(len(styles), 3)
        style_ids = [s["style_id"] for s in styles]
        self.assertIn("neutral", style_ids)
        self.assertIn("serious", style_ids)
        self.assertIn("storytelling", style_ids)

    def test_03_tts_synthesis_standard(self):
        payload = {
            "text": "Chào bạn, đây là thử nghiệm tổng hợp tiếng Việt với API FastAPI.",
            "style_id": "storytelling",
            "speed": 1.0
        }
        resp = client.post("/tts", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_characters"], 0)
        self.assertGreater(data["total_chunks"], 0)
        self.assertIsNotNone(data["audio_file"])
        self.assertTrue(os.path.exists(os.path.join(OUTPUTS_DIR, data["audio_file"])))

        # Clean up output file
        del_resp = client.delete(f"/outputs/{data['audio_file']}")
        self.assertEqual(del_resp.status_code, 200)

    def test_04_tts_exceed_max_chars_validation(self):
        """Ensure text exceeding 5,000 chars is rejected."""
        long_payload = {
            "text": "A" * 5001,
            "style_id": "neutral"
        }
        resp = client.post("/tts", json=long_payload)
        self.assertIn(resp.status_code, [400, 422])

    def test_05_voice_analyze_endpoint(self):
        # Create small synthetic WAV in memory
        sr = TARGET_SAMPLE_RATE
        samples = [int(10000 * math.sin(2 * math.pi * 440 * i / sr)) for i in range(sr * 3)]
        
        temp_wav_path = os.path.join(OUTPUTS_DIR, "test_upload_sample.wav")
        AudioProcessor.write_wav_pcm16(temp_wav_path, samples, sample_rate=sr)

        with open(temp_wav_path, "rb") as f:
            resp = client.post("/voices/analyze", files={"file": ("test_upload_sample.wav", f, "audio/wav")})
        
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["sample_rate"], TARGET_SAMPLE_RATE)
        self.assertEqual(data["channels"], 1)
        self.assertTrue(2.8 <= data["total_duration_sec"] <= 3.2)

    def test_06_security_path_traversal_prevention(self):
        resp = client.get("/outputs/..%2F..%2Fsecret.txt")
        self.assertIn(resp.status_code, [404, 400])

    def test_07_frontend_index_serving(self):
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("LAPQUE Personal Vietnamese TTS Studio", resp.text)

if __name__ == "__main__":
    unittest.main()
