"""Deterministic Vietnamese Text Normalizer for TTS Frontend.
Converts:
- Numbers (integers, floats, negative, phone numbers)
- Dates (dd/mm/yyyy, dd-mm-yyyy, dd/mm)
- Currency (VNĐ, đ, USD, EUR, $, k/K)
- Percentages (%)
- Units and Abbreviations (TP.HCM, HN, PGS, TS, BS, km, kg, m2, v.v., etc.)
- Punctuations & whitespace normalization
Preserves Vietnamese tonal integrity (hỏi/ngã/nặng/sắc/huyền).
"""
import re
import unicodedata
from typing import List, Dict

DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
UNITS_3 = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]

ABBREVIATIONS = [
    (r"\bTP\.\s*HCM\b", "Thành phố Hồ Chí Minh"),
    (r"\bTPHCM\b", "Thành phố Hồ Chí Minh"),
    (r"\bHN\b", "Hà Nội"),
    (r"\bĐH\b", "Đại học"),
    (r"\bPGS\.\s*TS\.?\b", "Phó giáo sư Tiến sĩ"),
    (r"\bPGS\.(?=\s|$)", "Phó giáo sư"),
    (r"\bPGS\b", "Phó giáo sư"),
    (r"\bTS\.(?=\s|$)", "Tiến sĩ"),
    (r"\bTS\b", "Tiến sĩ"),
    (r"\bThS\.(?=\s|$)", "Thạc sĩ"),
    (r"\bThS\b", "Thạc sĩ"),
    (r"\bBS\.(?=\s|$)", "Bác sĩ"),
    (r"\bBS\b", "Bác sĩ"),
    (r"\bv\.v\.?", "vân vân"),
    (r"\bv/v\b", "về việc"),
    (r"\bKTS\.(?=\s|$)", "Kiến trúc sư"),
    (r"\bKTS\b", "Kiến trúc sư"),
    (r"\bUBND\b", "Ủy ban nhân dân"),
    (r"\bHĐND\b", "Hội đồng nhân dân"),
    (r"\bBCH\b", "Ban chấp hành"),
    (r"\bTW\b", "Trung ương"),
    (r"\bTNHH\b", "Trách nhiệm hữu hạn"),
    (r"\bCP\b", "Cổ phần"),
    (r"\bCLB\b", "Câu lạc bộ"),
    (r"\bkm/h\b", "ki lô mét trên giờ"),
    (r"\bkm2\b", "ki lô mét vuông"),
    (r"\bkm²\b", "ki lô mét vuông"),
    (r"\bkm\b", "ki lô mét"),
    (r"\bcm\b", "xen ti mét"),
    (r"\bmm\b", "mi li mét"),
    (r"\bm2\b", "mét vuông"),
    (r"\bm²\b", "mét vuông"),
    (r"\bm3\b", "mét khối"),
    (r"\bm³\b", "mét khối"),
    (r"\bha\b", "héc ta"),
    (r"\bkg\b", "ki lô gam"),
    (r"\bgr\b", "gam"),
    (r"\bg\b", "gam"),
    (r"\bml\b", "mi li lít"),
    (r"\bl\b", "lít"),
]

class VietnameseNormalizer:
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Standardize Unicode to NFC form (precomposed characters)."""
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    @classmethod
    def read_three_digits(cls, num_str: str, has_higher_unit: bool = False) -> str:
        """Reads a 1-3 digit string (e.g. '123' -> 'một trăm hai mươi ba')."""
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []

        if h > 0 or has_higher_unit:
            res.append(DIGITS[h] + " trăm")

        if t == 0:
            if u > 0:
                if h > 0 or has_higher_unit:
                    res.append("linh " + DIGITS[u])
                else:
                    res.append(DIGITS[u])
        elif t == 1:
            res.append("mười")
            if u == 5:
                res.append("lăm")
            elif u > 0:
                res.append(DIGITS[u])
        else:
            res.append(DIGITS[t] + " mươi")
            if u == 1:
                res.append("mốt")
            elif u == 4:
                res.append("tư")
            elif u == 5:
                res.append("lăm")
            elif u > 0:
                res.append(DIGITS[u])

        if not res:
            return "không" if not has_higher_unit else ""
        return " ".join(res).strip()

    @classmethod
    def read_integer(cls, num_int: int) -> str:
        """Reads any non-negative integer into standard Vietnamese words."""
        if num_int == 0:
            return "không"
        
        s = str(abs(num_int))
        # Split into groups of 3 from right to left
        groups = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        
        words = []
        for i, grp in enumerate(groups):
            grp_int = int(grp)
            if grp_int == 0:
                continue
            has_higher = (i < len(groups) - 1)
            grp_words = cls.read_three_digits(grp, has_higher_unit=has_higher)
            unit = UNITS_3[i % len(UNITS_3)]
            if unit:
                words.append(f"{grp_words} {unit}")
            else:
                words.append(grp_words)
        
        words.reverse()
        return " ".join(words).strip()

    @classmethod
    def normalize_currency(cls, text: str) -> str:
        """Converts currency patterns like '50.000 VNĐ', '500k', '$100', '100 USD'."""
        # 500k / 50k
        def rep_k(m):
            val = int(m.group(1)) * 1000
            return cls.read_integer(val) + " đồng"
        text = re.sub(r"\b(\d+)\s*[kK]\b", rep_k, text)

        # $100 or 100$
        def rep_usd_sym(m):
            val = cls.parse_and_read_number(m.group(1).replace(".", "").replace(",", "."))
            return f"{val} đô la"
        text = re.sub(r"\$\s*([\d\.,]+)", rep_usd_sym, text)
        text = re.sub(r"([\d\.,]+)\s*\$", rep_usd_sym, text)

        # 100 USD / EUR / VND / VNĐ
        def rep_curr_code(m):
            val = cls.parse_and_read_number(m.group(1).replace(".", "").replace(",", "."))
            code = m.group(2).upper()
            curr_map = {"USD": "đô la", "EUR": "ơ-rô", "VND": "đồng", "VNĐ": "đồng", "Đ": "đồng"}
            return f"{val} {curr_map.get(code, code)}"
        text = re.sub(r"([\d\.,]+)\s*(USD|EUR|VND|VNĐ|đ)\b", rep_curr_code, text, flags=re.IGNORECASE)

        return text

    @classmethod
    def normalize_percentages(cls, text: str) -> str:
        """Converts '50%', '12.5%' to 'năm mươi phần trăm'."""
        def rep_pct(m):
            num_str = m.group(1).replace(",", ".")
            num_word = cls.parse_and_read_number(num_str)
            return f"{num_word} phần trăm"
        return re.sub(r"([\d\.,]+)\s*%", rep_pct, text)

    @classmethod
    def normalize_dates(cls, text: str) -> str:
        """Converts dd/mm/yyyy, dd-mm-yyyy, dd/mm."""
        def rep_full_date(m):
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            day_word = "hai mươi tư" if day == 24 else cls.read_integer(day)
            month_word = cls.read_integer(month)
            year_word = cls.read_integer(year)
            return f"ngày {day_word} tháng {month_word} năm {year_word}"
        text = re.sub(r"(?i)(?:\bngày\s+)?(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b", rep_full_date, text)

        def rep_short_date(m):
            day, month = int(m.group(1)), int(m.group(2))
            if 1 <= day <= 31 and 1 <= month <= 12:
                day_word = "hai mươi tư" if day == 24 else cls.read_integer(day)
                return f"ngày {day_word} tháng {cls.read_integer(month)}"
            return m.group(0)
        text = re.sub(r"(?i)(?:\bngày\s+)?(\d{1,2})[\/\-](\d{1,2})\b", rep_short_date, text)

        return text

    @classmethod
    def parse_and_read_number(cls, s: str) -> str:
        """Parse string containing integer or float."""
        s = s.strip()
        is_negative = s.startswith("-")
        if is_negative:
            s = s[1:]
        
        prefix = "âm " if is_negative else ""

        if "." in s or "," in s:
            # Float
            parts = re.split(r"[\.,]", s, maxsplit=1)
            int_part = int(parts[0]) if parts[0] else 0
            dec_part = parts[1]
            dec_words = " ".join([DIGITS[int(d)] for d in dec_part if d.isdigit()])
            return f"{prefix}{cls.read_integer(int_part)} phẩy {dec_words}".strip()
        else:
            try:
                val = int(s)
                return f"{prefix}{cls.read_integer(val)}".strip()
            except ValueError:
                return s

    @classmethod
    def normalize_numbers(cls, text: str) -> str:
        """Converts standalone integers, floats, and negative numbers."""
        # Thousands formatted with dots: 100.000 -> 100000
        text = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: m.group(1).replace(".", ""), text)

        # Standard numbers (e.g. 123, -5, 3.14, 3,14)
        def rep_num(m):
            num_str = m.group(0)
            return cls.parse_and_read_number(num_str)

        # Match numbers with optional decimal/negative
        text = re.sub(r"(?<![a-zA-Z0-9_\/])[-+]?\d+(?:[\.,]\d+)?(?![a-zA-Z0-9_\/])", rep_num, text)
        return text

    @classmethod
    def normalize_abbreviations(cls, text: str) -> str:
        """Replaces common abbreviations with full spoken Vietnamese words."""
        for pattern, replacement in ABBREVIATIONS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @classmethod
    def normalize_punctuations(cls, text: str) -> str:
        """Standardize punctuation marks to create natural prosodic pauses."""
        # Replace quotes and special brackets with pauses / commas
        text = re.sub(r"[\"“”«»]", "", text)
        text = re.sub(r"[\(\)\[\]\{\}]", ", ", text)
        text = re.sub(r"\s*:\s*", ", ", text)
        text = re.sub(r"\s*;\s*", ", ", text)
        text = re.sub(r"\s*—\s*", ", ", text)
        text = re.sub(r"\s*–\s*", ", ", text)
        text = re.sub(r"\s*-\s*", ", ", text)

        # Consolidate multiple punctuation marks (e.g. '??' -> '?', '...' -> '.')
        text = re.sub(r"\.{2,}", ".", text)
        text = re.sub(r"\?{2,}", "?", text)
        text = re.sub(r"!{2,}", "!", text)
        text = re.sub(r",{2,}", ",", text)

        # Ensure space after punctuation
        text = re.sub(r"\s*([.,?!])\s*", r"\1 ", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def normalize(cls, text: str) -> str:
        """Full deterministic pipeline: Unicode NFC -> Abbreviations -> Dates -> Currency -> Percentages -> Numbers -> Punctuations."""
        if not text or not isinstance(text, str):
            return ""
        
        # 1. Unicode NFC
        t = cls.normalize_unicode(text)
        # 2. Abbreviations & Units
        t = cls.normalize_abbreviations(t)
        # 3. Dates
        t = cls.normalize_dates(t)
        # 4. Currency
        t = cls.normalize_currency(t)
        # 5. Percentages
        t = cls.normalize_percentages(t)
        # 6. Standalone Numbers
        t = cls.normalize_numbers(t)
        # 7. Punctuations & Whitespace
        t = cls.normalize_punctuations(t)

        return t
