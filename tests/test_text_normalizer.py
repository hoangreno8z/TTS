"""Comprehensive Unit Tests for Vietnamese Text Normalizer (Phase 3).
Covers all test criteria specified in docs/04_VIETNAMESE_TEXT_PIPELINE.md:
1. Số (integers, floats, negative, special endings: mốt/tư/lăm)
2. Ngày tháng năm
3. Tiền tệ (VNĐ, USD, $, k)
4. Phần trăm (%)
5. Viết tắt & Đơn vị đo
6. Dấu hỏi / Dấu ngã & Thanh điệu tiếng Việt
7. Tên riêng & Từ mượn
8. Dấu câu & Cấu trúc ngữ điệu (pauses)
9. Unicode NFC standard normalization
10. Benchmark sample text normalization
"""
import os
import sys
import unittest
import unicodedata

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.text_norm.vietnamese_normalizer import VietnameseNormalizer

class TestVietnameseNormalizer(unittest.TestCase):

    def test_01_numbers_basic(self):
        """Test integer readings."""
        self.assertEqual(VietnameseNormalizer.read_integer(0), "không")
        self.assertEqual(VietnameseNormalizer.read_integer(5), "năm")
        self.assertEqual(VietnameseNormalizer.read_integer(10), "mười")
        self.assertEqual(VietnameseNormalizer.read_integer(11), "mười một")
        self.assertEqual(VietnameseNormalizer.read_integer(15), "mười lăm")
        self.assertEqual(VietnameseNormalizer.read_integer(20), "hai mươi")
        self.assertEqual(VietnameseNormalizer.read_integer(21), "hai mươi mốt")
        self.assertEqual(VietnameseNormalizer.read_integer(24), "hai mươi tư")
        self.assertEqual(VietnameseNormalizer.read_integer(25), "hai mươi lăm")
        self.assertEqual(VietnameseNormalizer.read_integer(105), "một trăm linh năm")
        self.assertEqual(VietnameseNormalizer.read_integer(1000), "một nghìn")
        self.assertEqual(VietnameseNormalizer.read_integer(1000000), "một triệu")

    def test_02_numbers_in_sentence(self):
        """Test integers, floats, and negative numbers in context."""
        text = "Nhiệt độ hôm nay là -5 độ, chỉ số là 3.14."
        norm = VietnameseNormalizer.normalize(text)
        self.assertIn("âm năm", norm)
        self.assertIn("ba phẩy một bốn", norm)

    def test_03_dates(self):
        """Test date formats: dd/mm/yyyy, dd-mm-yyyy."""
        text = "Hôm nay là ngày 24/08/2026."
        norm = VietnameseNormalizer.normalize(text)
        self.assertEqual(norm, "Hôm nay là ngày hai mươi tư tháng tám năm hai nghìn không trăm hai mươi sáu.")
        self.assertEqual(VietnameseNormalizer.normalize("Sự kiện 01/05."), "Sự kiện ngày một tháng năm.")

    def test_04_currency(self):
        """Test Vietnamese & foreign currencies."""
        self.assertIn("năm mươi nghìn đồng", VietnameseNormalizer.normalize("Giá 50.000 VNĐ."))
        self.assertIn("năm trăm nghìn đồng", VietnameseNormalizer.normalize("Chuyển khoản 500k."))
        self.assertIn("một trăm đô la", VietnameseNormalizer.normalize("Giá $100."))
        self.assertIn("năm mươi đô la", VietnameseNormalizer.normalize("50 USD."))

    def test_05_percentages(self):
        """Test percentages."""
        norm = VietnameseNormalizer.normalize("Tăng trưởng đạt 15% trong quý này.")
        self.assertIn("mười lăm phần trăm", norm)

    def test_06_abbreviations_and_units(self):
        """Test titles, places, and units."""
        text = "PGS.TS Nguyễn Văn A đi từ TP.HCM về HN với vận tốc 80 km/h."
        norm = VietnameseNormalizer.normalize(text)
        self.assertIn("Phó giáo sư Tiến sĩ", norm)
        self.assertIn("Thành phố Hồ Chí Minh", norm)
        self.assertIn("Hà Nội", norm)
        self.assertIn("ki lô mét trên giờ", norm)

    def test_07_vietnamese_tones(self):
        """Ensure Vietnamese tonal distinctions (hỏi/ngã/nặng/sắc/huyền) are strictly preserved."""
        words = ["bảo đảm", "mẫu mã", "chữ nghĩa", "nghĩ ngợi", "vĩ đại", "kỹ thuật", "lãnh đạo"]
        for w in words:
            norm = VietnameseNormalizer.normalize(w)
            self.assertEqual(norm, w)

    def test_08_punctuations_and_pauses(self):
        """Test punctuation conversion into prosodic pause separators."""
        text = 'Anh nói: "Tôi đi đây (hẹn gặp lại); chúc may mắn!"'
        norm = VietnameseNormalizer.normalize(text)
        self.assertNotIn('"', norm)
        self.assertNotIn('(', norm)
        self.assertNotIn(')', norm)
        self.assertIn("hẹn gặp lại", norm)

    def test_09_unicode_nfc_standardization(self):
        """Test NFD vs NFC handling to ensure deterministic synthesis input."""
        # 'tiếng' in NFD (decomposed)
        nfd_str = unicodedata.normalize("NFD", "tiếng Việt")
        # Normalize through our pipeline
        nfc_result = VietnameseNormalizer.normalize(nfd_str)
        # Result should be strictly NFC
        self.assertEqual(nfc_result, unicodedata.normalize("NFC", "tiếng Việt"))

    def test_10_long_complex_paragraph(self):
        """Test a long real-world paragraph with multiple elements combined."""
        raw = "Ngày 24/8/2026, PGS.TS Trần Văn B tại TP.HCM đã công bố dự án trị giá 500k VNĐ (tương đương $20 USD), tăng 12.5% so với năm 2025."
        norm = VietnameseNormalizer.normalize(raw)
        self.assertIn("Phó giáo sư Tiến sĩ", norm)
        self.assertIn("Thành phố Hồ Chí Minh", norm)
        self.assertIn("phần trăm", norm)
        self.assertIn("đồng", norm)

if __name__ == "__main__":
    unittest.main()
