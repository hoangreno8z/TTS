import os
import time
import json
import urllib.request
import urllib.error
import asyncio
from typing import Tuple, Dict, Any, Optional
import edge_tts

class VoiceCascadeEngine:
    _instance = None

    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.fish_audio_key = os.getenv("FISH_AUDIO_API_KEY", "")
        self.playht_key = os.getenv("PLAYHT_API_KEY", "")
        self.disabled_until = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VoiceCascadeEngine()
        return cls._instance

    def set_keys(self, elevenlabs_key: str = "", fish_audio_key: str = "", playht_key: str = ""):
        if elevenlabs_key: self.elevenlabs_key = elevenlabs_key
        if fish_audio_key: self.fish_audio_key = fish_audio_key
        if playht_key: self.playht_key = playht_key

    def _is_available(self, provider: str) -> bool:
        until = self.disabled_until.get(provider, 0)
        return time.time() > until

    def _mark_rate_limited(self, provider: str, cooldown_seconds: int = 300):
        self.disabled_until[provider] = time.time() + cooldown_seconds
        print(f"[VoiceCascade] {provider} quota reached or rate limited. Paused for {cooldown_seconds}s.")

    # 1. Tier 1: ElevenLabs API (King of Quality)
    def _call_elevenlabs(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", user_key: Optional[str] = None) -> Optional[bytes]:
        key = user_key or self.elevenlabs_key
        if not key or not self._is_available("elevenlabs"):
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": key,
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.2,
                "use_speaker_boost": True
            }
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 402, 401):
                self._mark_rate_limited("elevenlabs", cooldown_seconds=3600)
            return None
        except Exception:
            return None

    # 2. Tier 2: Fish Audio API (Fish Speech v1.5 - 10k chars/day)
    def _call_fish_audio(self, text: str, reference_id: Optional[str] = None, user_key: Optional[str] = None) -> Optional[bytes]:
        key = user_key or self.fish_audio_key
        if not key or not self._is_available("fish_audio"):
            return None

        url = "https://api.fish.audio/v1/tts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text,
            "reference_id": reference_id or "default",
            "format": "mp3",
            "mp3_bitrate": 128,
            "latency": "normal"
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=7.0) as resp:
                if resp.status == 200:
                    return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 402, 401):
                self._mark_rate_limited("fish_audio", cooldown_seconds=1800)
            return None
        except Exception:
            return None

    # 3. Tier 3: Edge-TTS High-Def Neural (Infinite 100% Free Fallback)
    async def _call_edge_tts_async(self, text: str, voice_name: str = "vi-VN-NamMinhNeural", speed: float = 1.0) -> Optional[bytes]:
        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "+0%"
        try:
            comm = edge_tts.Communicate(text=text, voice=voice_name, rate=rate_str)
            audio_chunks = []
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            if audio_chunks:
                return b"".join(audio_chunks)
        except Exception as e:
            print(f"[VoiceCascade] EdgeTTS notice: {e}")
        return None

    # 4. Master Synthesize with Waterfall Cascade
    async def synthesize(
        self,
        text: str,
        style_id: str = "neutral",
        voice_gender: str = "male",
        speed: float = 1.0,
        custom_keys: Optional[Dict[str, str]] = None
    ) -> Tuple[bytes, str, str, float]:
        t0 = time.time()
        keys = custom_keys or {}

        # 1. Tier 1: Try ElevenLabs
        eleven_bytes = self._call_elevenlabs(text, user_key=keys.get("elevenlabs"))
        if eleven_bytes:
            return eleven_bytes, "mp3", "ElevenLabs API (Tier 1 - Vua Chất Lượng)", round(time.time() - t0, 3)

        # 2. Tier 2: Try Fish Audio
        fish_bytes = self._call_fish_audio(text, user_key=keys.get("fish_audio"))
        if fish_bytes:
            return fish_bytes, "mp3", "Fish Audio API (Tier 2 - Fish Speech)", round(time.time() - t0, 3)

        # 3. Tier 4 (Final Shield): Edge-TTS Neural Fallback (Infinite)
        voice_choice = "vi-VN-HoaiMyNeural" if voice_gender == "female" else "vi-VN-NamMinhNeural"
        edge_bytes = await self._call_edge_tts_async(text, voice_choice, speed=speed)
        if edge_bytes:
            return edge_bytes, "mp3", "Edge-TTS Neural (Tier 4 - Vô Hạn Miễn Phí)", round(time.time() - t0, 3)

        # Extreme fallback
        return b"", "mp3", "Failed all providers", round(time.time() - t0, 3)
