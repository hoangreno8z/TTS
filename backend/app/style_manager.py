"""Style Profile Manager for LAPQUE Vietnamese TTS.
Defines and manages default and custom voice styles:
- Default: neutral, serious, storytelling
- Custom: supports adding any character/voice style (e.g. lali5, anime_voice, custom_host)
Supports persistent storage in config/custom_styles.json and dynamic directory management.
"""
import os
import glob
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

@dataclass
class StyleProfile:
    style_id: str
    name: str
    description: str
    speed: float = 1.0
    pause_multiplier: float = 1.0
    pitch_adjustment: float = 0.0
    energy_adjustment: float = 1.0
    prompt_context: str = ""
    ref_audio_subfolder: str = "neutral"
    checkpoint_path: Optional[str] = None
    acoustic_profile: Optional[Dict[str, Any]] = None

DEFAULT_STYLES: Dict[str, StyleProfile] = {
    "loc_dinh_ky": StyleProfile(
        style_id="loc_dinh_ky",
        name="Lộc Đỉnh Ký",
        description="Lồng tiếng Châu Tinh Trì",
        speed=1.0,
        pause_multiplier=1.0,
        pitch_adjustment=0.0,
        energy_adjustment=1.0,
        prompt_context="[Phong cách Lộc Đỉnh Ký]",
        ref_audio_subfolder="loc_dinh_ky"
    ),
    "neutral": StyleProfile(
        style_id="neutral",
        name="Mặc Định",
        description="Giọng nam chuẩn tiếng Việt",
        speed=1.0,
        pause_multiplier=1.0,
        pitch_adjustment=0.0,
        energy_adjustment=1.0,
        prompt_context="[Phong cách mặc định]",
        ref_audio_subfolder="neutral"
    ),
    "storytelling": StyleProfile(
        style_id="storytelling",
        name="Kể Chuyện",
        description="Giọng đọc truyền cảm",
        speed=1.05,
        pause_multiplier=1.1,
        pitch_adjustment=0.3,
        energy_adjustment=1.15,
        prompt_context="[Phong cách kể chuyện]",
        ref_audio_subfolder="storytelling"
    ),
    "serious": StyleProfile(
        style_id="serious",
        name="Nghiêm Túc",
        description="Giọng trầm ổn, trang trọng",
        speed=0.92,
        pause_multiplier=1.25,
        pitch_adjustment=-0.5,
        energy_adjustment=0.95,
        prompt_context="[Phong cách nghiêm túc]",
        ref_audio_subfolder="serious"
    )
}

class StyleManager:
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.custom_styles_file = os.path.join(self.project_root, "config", "custom_styles.json")
        self.styles: Dict[str, StyleProfile] = dict(DEFAULT_STYLES)
        self.load_custom_styles()

    def load_custom_styles(self):
        """Load any user-defined custom styles from config/custom_styles.json."""
        if os.path.exists(self.custom_styles_file):
            try:
                with open(self.custom_styles_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, item in data.items():
                        self.styles[sid.lower()] = StyleProfile(**item)
            except Exception as e:
                print(f"Warning: Could not load custom styles: {e}")

    def save_custom_styles(self):
        """Save custom styles to config/custom_styles.json."""
        custom_data = {}
        for sid, prof in self.styles.items():
            if sid not in DEFAULT_STYLES:
                custom_data[sid] = asdict(prof)

        os.makedirs(os.path.dirname(self.custom_styles_file), exist_ok=True)
        with open(self.custom_styles_file, "w", encoding="utf-8") as f:
            json.dump(custom_data, f, indent=2, ensure_ascii=False)

    def add_custom_style(
        self,
        style_id: str,
        name: str,
        description: str,
        speed: float = 1.0,
        pause_multiplier: float = 1.0,
        pitch_adjustment: float = 0.0,
        energy_adjustment: float = 1.0,
        prompt_context: str = "",
        checkpoint_path: Optional[str] = None
    ) -> StyleProfile:
        """Register and persist a new custom voice style (e.g. lali5)."""
        sid = style_id.lower().strip()
        subfolder = sid

        # Ensure directory structures exist for this style
        os.makedirs(os.path.join(self.project_root, "data", "raw", subfolder), exist_ok=True)
        os.makedirs(os.path.join(self.project_root, "data", "voice", subfolder), exist_ok=True)

        profile = StyleProfile(
            style_id=sid,
            name=name or f"Phong cách {sid}",
            description=description or f"Phong cách giọng tùy chỉnh: {sid}",
            speed=speed,
            pause_multiplier=pause_multiplier,
            pitch_adjustment=pitch_adjustment,
            energy_adjustment=energy_adjustment,
            prompt_context=prompt_context or f"[Phong cách {sid}]",
            ref_audio_subfolder=subfolder,
            checkpoint_path=checkpoint_path
        )
        self.styles[sid] = profile
        self.save_custom_styles()
        return profile

    def rename_style(self, style_id: str, new_name: str) -> bool:
        """Rename an existing style and save."""
        sid = style_id.lower().strip()
        self.load_custom_styles()
        if sid in self.styles:
            self.styles[sid].name = new_name.strip()
            self.save_custom_styles()
            
            # Update acoustic_profile.json if exists
            prof_json = os.path.join(self.project_root, "data", "voice", sid, "acoustic_profile.json")
            if os.path.exists(prof_json):
                try:
                    with open(prof_json, "r", encoding="utf-8") as fp:
                        p_data = json.load(fp)
                    p_data["style_name"] = new_name.strip()
                    with open(prof_json, "w", encoding="utf-8") as fp:
                        json.dump(p_data, fp, indent=2, ensure_ascii=False)
                except Exception:
                    pass
            return True
        return False

    def list_styles(self) -> List[Dict[str, Any]]:
        """List all available style profiles as JSON-serializable dictionaries including dynamic acoustic profiles."""
        self.load_custom_styles()
        # Also dynamically discover any styles created in data/voice/
        voice_dir = os.path.join(self.project_root, "data", "voice")
        if os.path.exists(voice_dir):
            for folder_name in os.listdir(voice_dir):
                sid = folder_name.lower().strip()
                prof_json = os.path.join(voice_dir, folder_name, "acoustic_profile.json")
                if os.path.exists(prof_json):
                    try:
                        with open(prof_json, "r", encoding="utf-8") as f_p:
                            p_data = json.load(f_p)
                        if sid not in self.styles:
                            self.styles[sid] = StyleProfile(
                                style_id=sid,
                                name=p_data.get("name", f"Style {folder_name.title()}"),
                                description=p_data.get("description", f"Style tự tạo từ mẫu giọng {folder_name}"),
                                speed=p_data.get("speed_rate", 1.0),
                                pitch_adjustment=p_data.get("pitch_adjustment", 0.0),
                                ref_audio_subfolder=sid,
                                acoustic_profile=p_data
                            )
                        else:
                            self.styles[sid].acoustic_profile = p_data
                    except Exception:
                        pass
        return [asdict(p) for p in self.styles.values()]

    def get_style(self, style_id: str) -> StyleProfile:
        """Retrieve a style profile by ID, defaulting to 'neutral' if unknown."""
        key = style_id.lower().strip() if style_id else "neutral"
        return self.styles.get(key, self.styles["neutral"])

    def resolve_reference_audio(self, style_id: str, custom_ref: Optional[str] = None) -> Optional[str]:
        """Find the best reference audio for a given style."""
        if custom_ref and os.path.exists(custom_ref):
            return custom_ref

        style = self.get_style(style_id)
        style_dir = os.path.join(self.project_root, "data", "voice", style.ref_audio_subfolder)
        
        # 1. Search in target style folder
        if os.path.exists(style_dir):
            wavs = glob.glob(os.path.join(style_dir, "*.wav"))
            if wavs:
                return wavs[0]

        # 2. Fallback to neutral
        neutral_dir = os.path.join(self.project_root, "data", "voice", "neutral")
        if os.path.exists(neutral_dir):
            wavs = glob.glob(os.path.join(neutral_dir, "*.wav"))
            if wavs:
                return wavs[0]

        # 3. Fallback to any wav in data/voice
        all_wavs = glob.glob(os.path.join(self.project_root, "data", "voice", "**", "*.wav"), recursive=True)
        if all_wavs:
            return all_wavs[0]

        return None
