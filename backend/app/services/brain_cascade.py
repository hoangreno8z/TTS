import os
import re
import time
import json
import urllib.request
import urllib.error
from typing import Tuple, Dict, Any, Optional

class LocalVietnameseNormalizer:
    NUM_DICT = {
        '0': 'không', '1': 'một', '2': 'hai', '3': 'ba', '4': 'bốn',
        '5': 'năm', '6': 'sáu', '7': 'bảy', '8': 'tám', '9': 'chín'
    }

    ABBR_DICT = {
        'tks': 'cảm ơn', 'thx': 'cảm ơn', 'cam on': 'cảm ơn',
        'ko': 'không', 'k': 'không', 'hok': 'không', 'khum': 'không',
        'dc': 'được', 'đc': 'được', 'dk': 'được',
        'bt': 'biết', 'bít': 'biết',
        'ng': 'người', 'ngta': 'người ta',
        'j': 'gì', 'gi': 'gì',
        'vs': 'với', 'w': 'với',
        'h': 'giờ', 'h/nay': 'hôm nay',
        'mn': 'mọi người',
        'a': 'anh', 'e': 'em', 'c': 'chị',
        'ad': 'quản trị viên'
    }

    @classmethod
    def normalize_currency(cls, text: str) -> str:
        def replace_k(m):
            num = m.group(1)
            return f"{num} nghìn đồng"
        def replace_tr(m):
            num = m.group(1)
            return f"{num} triệu đồng"
        
        text = re.sub(r'(\d+)\s*(?:k|K)\b', replace_k, text)
        text = re.sub(r'(\d+)\s*(?:tr|TR|củ)\b', replace_tr, text)
        text = re.sub(r'(\d+)\s*(?:đ|vnd|VND|đồng)\b', r'\1 đồng', text)
        return text

    @classmethod
    def normalize_dates(cls, text: str) -> str:
        def replace_date_full(m):
            d, mth, y = m.group(1), m.group(2), m.group(3)
            return f"ngày {int(d)} tháng {int(mth)} năm {y}"
        def replace_date_short(m):
            d, mth = m.group(1), m.group(2)
            return f"ngày {int(d)} tháng {int(mth)}"

        text = re.sub(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})', replace_date_full, text)
        text = re.sub(r'(\d{1,2})[\/\-](\d{1,2})', replace_date_short, text)
        return text

    @classmethod
    def normalize_abbreviations(cls, text: str) -> str:
        words = text.split()
        normalized_words = []
        for w in words:
            clean_w = re.sub(r'[^\w\s]', '', w).lower()
            if clean_w in cls.ABBR_DICT:
                sub = cls.ABBR_DICT[clean_w]
                punct = re.sub(r'[\w\s]', '', w)
                normalized_words.append(sub + punct)
            else:
                normalized_words.append(w)
        return " ".join(normalized_words)

    @classmethod
    def process(cls, text: str) -> str:
        text = cls.normalize_currency(text)
        text = cls.normalize_dates(text)
        text = cls.normalize_abbreviations(text)
        return text.strip()


class BrainCascadeEngine:
    _instance = None

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.nvidia_key = os.getenv("NVIDIA_NIM_API_KEY", "")
        self.disabled_until = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrainCascadeEngine()
        return cls._instance

    def set_keys(self, gemini_key: str = "", groq_key: str = "", nvidia_key: str = ""):
        if gemini_key: self.gemini_key = gemini_key
        if groq_key: self.groq_key = groq_key
        if nvidia_key: self.nvidia_key = nvidia_key

    def _is_available(self, provider: str) -> bool:
        until = self.disabled_until.get(provider, 0)
        return time.time() > until

    def _mark_rate_limited(self, provider: str, cooldown_seconds: int = 60):
        self.disabled_until[provider] = time.time() + cooldown_seconds
        print(f"[BrainCascade] {provider} rate limited. Paused for {cooldown_seconds}s.")

    # 1. Tier 1: Google Gemini
    def _call_gemini(self, text: str, user_key: Optional[str] = None) -> Optional[str]:
        key = user_key or self.gemini_key
        if not key or not self._is_available("gemini"):
            return None
        
        prompt = (
            "Ban la bo nao chuan hoa van ban tieng Viet cho he thong giong noi (TTS). "
            "Nhiem vu: Chuyen toan bo so, ngay thang, viet tat, tieng long sang chu tieng Viet tron vanh ro chu. "
            "Giu nguyen phong cach tu nhien, them dau phay ngat nghi thich hop. Chi tra ve duy nhat cau da chuan hoa.\n"
            f"Cau can chuan hoa: \"{text}\""
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return result.replace('"', '').strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 402):
                self._mark_rate_limited("gemini", cooldown_seconds=60)
            return None
        except Exception:
            return None

    # 2. Tier 2: Groq Cloud Llama 3.3 70B
    def _call_groq(self, text: str, user_key: Optional[str] = None) -> Optional[str]:
        key = user_key or self.groq_key
        if not key or not self._is_available("groq"):
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "Ban la bo nao chuan hoa van ban tieng Viet cho he thong doc TTS. Chuyen doi toan bo so, ngay thang, tu viet tat thanh chu viet chuan tieng Viet. Chi tra ve duy nhat cau da chuan hoa khong kem loi giai thich."
                },
                {"role": "user", "content": text}
            ],
            "temperature": 0.2,
            "max_tokens": 250
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data["choices"][0]["message"]["content"].strip().replace('"', '')
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 402):
                self._mark_rate_limited("groq", cooldown_seconds=60)
            return None
        except Exception:
            return None

    # 3. Tier 3: NVIDIA NIM
    def _call_nvidia(self, text: str, user_key: Optional[str] = None) -> Optional[str]:
        key = user_key or self.nvidia_key
        if not key or not self._is_available("nvidia"):
            return None

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        payload = {
            "model": "meta/llama-3.3-70b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "Chuan hoa so, ngay thang, viet tat tieng Viet cho giong doc TTS. Chi tra ve ket qua duy nhat."
                },
                {"role": "user", "content": text}
            ],
            "temperature": 0.2,
            "max_tokens": 250
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data["choices"][0]["message"]["content"].strip().replace('"', '')
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 402):
                self._mark_rate_limited("nvidia", cooldown_seconds=60)
            return None
        except Exception:
            return None

    # 4. Master Normalize with Waterfall Cascade
    def normalize(self, text: str, custom_keys: Optional[Dict[str, str]] = None) -> Tuple[str, str, float]:
        t0 = time.time()
        keys = custom_keys or {}
        
        # 1. Try Gemini (Tier 1)
        res = self._call_gemini(text, keys.get("gemini"))
        if res:
            return res, "Gemini 2.0 Flash (Tier 1)", round(time.time() - t0, 3)

        # 2. Try Groq (Tier 2)
        res = self._call_groq(text, keys.get("groq"))
        if res:
            return res, "Groq Llama 3.3 (Tier 2)", round(time.time() - t0, 3)

        # 3. Try Nvidia NIM (Tier 3)
        res = self._call_nvidia(text, keys.get("nvidia"))
        if res:
            return res, "NVIDIA NIM (Tier 3)", round(time.time() - t0, 3)

        # 4. Fallback to Local Regex (Tier 4 - Offline Infinite)
        res = LocalVietnameseNormalizer.process(text)
        return res, "Local Rule Engine (Tier 4 - Offline)", round(time.time() - t0, 3)
