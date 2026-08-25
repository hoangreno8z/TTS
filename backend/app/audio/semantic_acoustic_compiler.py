import os
import json
import re
from typing import Dict, Any, Optional

class SemanticAcousticCompiler:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

    def compile_instruction(self, user_instruction: str) -> Dict[str, Any]:
        text = (user_instruction or '').strip()
        if not text:
            return self._default_parameters()

        if self.api_key:
            try:
                res = self._call_gemini_api(text)
                if res:
                    return res
            except Exception:
                pass

        return self._rule_based_compilation(text)

    def _default_parameters(self) -> Dict[str, Any]:
        return {
            'target_pitch_delta_semitones': 0.0,
            'pitch_dynamics_factor': 1.0,
            'formant_f1_shift_hz': 0.0,
            'formant_f2_shift_hz': 0.0,
            'nasality_factor': 1.0,
            'sub_bass_gain_db': 0.0,
            'mid_presence_gain_db': 0.0,
            'air_treble_gain_db': 0.0,
            'speed_rate_modifier': 1.0,
            'speech_style_intent': 'Chun muc can bang',
            'acoustic_explanation': 'Giu nguyen pho am hoc goc'
        }

    def _rule_based_compilation(self, text: str) -> Dict[str, Any]:
        params = self._default_parameters()
        t = text.lower()
        explanations = []

        # 1. Pitch / Tone interpretation
        if any(w in t for w in ['tram', 'trầm', 'sau', 'sâu', 'day', 'dày', 'am', 'ấm', 'trầm ấm']):
            params['target_pitch_delta_semitones'] -= 2.2
            params['sub_bass_gain_db'] += 3.5
            explanations.append('Hạ cao độ F0 -2.2 nốt, tăng dải trầm Sub +3.5dB')
        elif any(w in t for w in ['cao', 'the the', 'the thé', 'thanh', 'chua']):
            params['target_pitch_delta_semitones'] += 2.5
            params['air_treble_gain_db'] += 2.5
            explanations.append('Nâng cao độ F0 +2.5 nốt, tăng dải cao +2.5dB')

        # 2. Acting & Emotion style
        if any(w in t for w in ['hai huoc', 'hài hước', 'cham biem', 'châm biếm', 'tinh nghich', 'loc dinh ky', 'lộc đỉnh ký', 'treu nguoi', 'trêu ngươi']):
            params['pitch_dynamics_factor'] = 1.35
            params['formant_f2_shift_hz'] += 120.0
            params['speed_rate_modifier'] = 1.08
            explanations.append('Tăng biến thiên quãng giọng +35%, đẩy Formant F2 +120Hz tạo độ nhí nhảnh')
        elif any(w in t for w in ['nghiem tuc', 'nghiêm túc', 'trang trong', 'thoi su', 'thời sự']):
            params['pitch_dynamics_factor'] = 0.85
            params['sub_bass_gain_db'] += 1.5
            params['speed_rate_modifier'] = 0.95
            explanations.append('Giảm dao động ngữ điệu, tăng độ trầm đĩnh đạc')

        # 3. Nasal & Throat Resonance
        if any(w in t for w in ['giong mui', 'giọng mũi', 'nghet mui', 'nghẹt mũi', 'nghen nghen', 'nghẹn ngào']):
            params['nasality_factor'] = 1.4
            params['formant_f1_shift_hz'] += 80.0
            explanations.append('Khuếch đại cộng hưởng khoang mũi F1 +80Hz')
        elif any(w in t for w in ['khoang mieng', 'khoang miệng', 'mo ham', 'mở hàm']):
            params['formant_f1_shift_hz'] -= 60.0
            explanations.append('Mở rộng khoang vòm họng')

        # 4. Cleanliness & Crackle
        if any(w in t for w in ['trong', 'bot re', 'bớt rè', 'em', 'êm', 'muot', 'mượt', 'sach', 'sạch']):
            params['air_treble_gain_db'] -= 2.0
            explanations.append('Kích hoạt bộ lọc triệt tiêu nhiễu dải cao -2.0dB')

        # 5. Speed
        if any(w in t for w in ['nhanh', 'gap', 'gấp']):
            params['speed_rate_modifier'] = 1.15
            explanations.append('Tăng tốc độ đọc +15%')
        elif any(w in t for w in ['cham', 'chậm', 'thong tha', 'thong thả', 'tu ton', 'từ tốn']):
            params['speed_rate_modifier'] = 0.88
            explanations.append('Giảm tốc độ đọc -12%')

        params['speech_style_intent'] = 'Phong cach bien dich theo chi dao'
        params['acoustic_explanation'] = '; '.join(explanations) if explanations else 'Toi uu can bang theo pho mau'
        return params

    def _call_gemini_api(self, text: str) -> Optional[Dict[str, Any]]:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        prompt = (
            "Ban la AI Chuyen Gia Vat Ly Am Hoc. Hay bien dich yeu cau cua nguoi dung sang cac tham so am hoc sau:\n"
            f"Yeu cau: {text}\n"
            "Tra ve JSON gom: target_pitch_delta_semitones, pitch_dynamics_factor, formant_f1_shift_hz, "
            "formant_f2_shift_hz, nasality_factor, sub_bass_gain_db, mid_presence_gain_db, air_treble_gain_db, "
            "speed_rate_modifier, speech_style_intent, acoustic_explanation"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                raw_json = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_json)
        return None

acoustic_compiler = None
def get_semantic_compiler(api_key: Optional[str] = None):
    global acoustic_compiler
    if acoustic_compiler is None:
        acoustic_compiler = SemanticAcousticCompiler(api_key)
    return acoustic_compiler
