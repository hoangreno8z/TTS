"""Unit tests for Phase 2 Audio Pipeline and Metadata Builder."""
import os
import sys
import unittest
import math
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

# Import scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import runpy

class TestAudioPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data"))
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_wav = os.path.join(self.test_dir, "synth_test.wav")

        # Generate a synthetic 4-second sine wave at 440 Hz with silent pauses
        sr = TARGET_SAMPLE_RATE
        total_samples = []
        
        # 1. 0.5s silence
        total_samples.extend([0] * int(sr * 0.5))
        # 2. 3.5s tone (440Hz)
        for i in range(int(sr * 3.5)):
            val = int(16000 * math.sin(2 * math.pi * 440 * i / sr))
            total_samples.append(val)
        # 3. 0.5s silence
        total_samples.extend([0] * int(sr * 0.5))

        AudioProcessor.write_wav_pcm16(self.test_wav, total_samples, sample_rate=sr)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_wav):
            os.remove(self.test_wav)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_read_write_wav(self):
        samples, sr, channels = AudioProcessor.read_wav_pcm16(self.test_wav)
        self.assertEqual(sr, TARGET_SAMPLE_RATE)
        self.assertEqual(channels, 1)
        self.assertEqual(len(samples), int(TARGET_SAMPLE_RATE * 4.5))

    def test_trim_silence(self):
        samples, sr, _ = AudioProcessor.read_wav_pcm16(self.test_wav)
        trimmed = AudioProcessor.trim_silence(samples, sample_rate=sr, threshold=0.01)
        # Original is 4.5s; trimmed should be approx 3.5s
        trimmed_sec = len(trimmed) / float(sr)
        self.assertTrue(3.3 <= trimmed_sec <= 3.7, f"Trimmed duration {trimmed_sec}s outside expected range.")

    def test_segment_audio(self):
        samples, sr, _ = AudioProcessor.read_wav_pcm16(self.test_wav)
        segments = AudioProcessor.segment_audio(samples, sample_rate=sr, min_sec=2.0, max_sec=10.0)
        self.assertGreaterEqual(len(segments), 1)

if __name__ == "__main__":
    unittest.main()
