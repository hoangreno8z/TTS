"""Unit tests for Phase 9 Long Text Processing & Audio Merging Pipeline."""
import os
import sys
import unittest
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.long_text_processor import LongTextProcessor
from app.audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

class TestLongTextPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data_long"))
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        # Clean up test dir
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, f))
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_01_split_into_sentences(self):
        text = "Hôm nay trời nắng đẹp. Tôi đi dạo quanh hồ? Bạn có đi cùng không! Hãy đi nào."
        sents = LongTextProcessor.split_into_sentences(text)
        self.assertEqual(len(sents), 4)
        self.assertIn("Hôm nay trời nắng đẹp.", sents[0])

    def test_02_chunk_5000_chars(self):
        """Test splitting a realistic 5,000-character article."""
        paragraph = (
            "Trải qua hàng ngàn năm lịch sử dựng nước và giữ nước, dân tộc Việt Nam đã xây dựng nên "
            "một nền văn hiến rực rỡ, đậm đà bản sắc dân tộc. Tinh thần yêu nước nồng nàn, ý chí tự lực "
            "tự cường và lòng nhân ái bao la luôn là ngọn đuốc soi đường cho các thế hệ. "
        )
        # Repeat to create ~5,000 chars
        text_5000 = (paragraph * 20)[:5000]
        self.assertGreaterEqual(len(text_5000), 4500)

        chunks = LongTextProcessor.split_into_chunks(text_5000, max_chunk_chars=250)
        self.assertGreater(len(chunks), 15)

        for c in chunks:
            self.assertLessEqual(len(c), 300)
            self.assertTrue(c.strip())

        # Ensure no words are cut in the middle (chunks begin and end on word boundaries)
        for c in chunks:
            self.assertFalse(c.startswith(" "))
            self.assertFalse(c.endswith(" "))

    def test_03_merge_wav_chunks(self):
        """Test merging multiple WAV chunks with pause padding and continuity."""
        sr = TARGET_SAMPLE_RATE
        chunk1_path = os.path.join(self.test_dir, "chunk_1.wav")
        chunk2_path = os.path.join(self.test_dir, "chunk_2.wav")
        merged_path = os.path.join(self.test_dir, "merged.wav")

        # 1.0s sine wave for chunk 1
        samples1 = [int(12000 * math.sin(2 * math.pi * 440 * i / sr)) for i in range(sr)]
        # 1.0s sine wave for chunk 2
        samples2 = [int(12000 * math.sin(2 * math.pi * 880 * i / sr)) for i in range(sr)]

        AudioProcessor.write_wav_pcm16(chunk1_path, samples1, sample_rate=sr)
        AudioProcessor.write_wav_pcm16(chunk2_path, samples2, sample_rate=sr)

        # Merge with 300ms pause
        pause_ms = 300
        LongTextProcessor.merge_wav_files([chunk1_path, chunk2_path], merged_path, pause_ms=pause_ms, sample_rate=sr)

        # Verify merged audio properties
        merged_samples, merged_sr, channels = AudioProcessor.read_wav_pcm16(merged_path)
        self.assertEqual(merged_sr, sr)
        self.assertEqual(channels, 1)

        # Expected duration: 1.0s + 0.3s + 1.0s = 2.3s -> 2.3 * 24000 = 55200 samples
        expected_samples = 24000 + int(24000 * 0.3) + 24000
        self.assertEqual(len(merged_samples), expected_samples)

if __name__ == "__main__":
    unittest.main()
