"""Engine Factory & Registry for LAPQUE TTS.
Loads configuration from config/engines.yaml (or pure-Python YAML parser fallback)
and returns the active BaseTTSAdapter instance.
"""
import os
import re
from typing import Dict, Any, Optional

from .adapters.base_adapter import BaseTTSAdapter
from .adapters.f5_tts_adapter import F5TTSAdapter
from .adapters.gpt_sovits_adapter import GPTSoVITSAdapter

ADAPTER_REGISTRY = {
    "f5-tts": F5TTSAdapter,
    "gpt-sovits": GPTSoVITSAdapter
}

def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Lightweight pure-Python parser for standard configuration YAML."""
    data = {}
    cur_section = None
    cur_subsection = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        
        indent = len(raw_line) - len(raw_line.lstrip())

        # Match key-value: 'key: value' or 'key:'
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip() if len(parts) > 1 else ""

            # Remove quotes
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            elif v.lower() == "true":
                v = True
            elif v.lower() == "false":
                v = False
            elif v.isdigit():
                v = int(v)

            if indent == 0:
                cur_section = k
                cur_subsection = None
                data[cur_section] = v if v != "" else {}
            elif indent == 2:
                cur_subsection = k
                if isinstance(data.get(cur_section), dict):
                    data[cur_section][cur_subsection] = v if v != "" else {}
            elif indent >= 4:
                if cur_section and cur_subsection and isinstance(data.get(cur_section), dict):
                    if isinstance(data[cur_section].get(cur_subsection), dict):
                        data[cur_section][cur_subsection][k] = v
        elif line.startswith("- "):
            # List item
            item = line[2:].strip().strip("\"'")
            if cur_section:
                if isinstance(data.get(cur_section), list):
                    data[cur_section].append(item)
                elif data.get(cur_section) == {} or data.get(cur_section) == "":
                    data[cur_section] = [item]
                elif isinstance(data.get(cur_section), dict) and cur_subsection:
                    if isinstance(data[cur_section].get(cur_subsection), list):
                        data[cur_section][cur_subsection].append(item)
                    else:
                        data[cur_section][cur_subsection] = [item]

    return data

class EngineFactory:
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        if not config_path:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            config_path = os.path.join(root, "config", "engines.yaml")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                import yaml
                return yaml.safe_load(content) or {}
            except ImportError:
                return parse_simple_yaml(content)
        return {}

    @classmethod
    def get_selected_engine_name(cls, config_path: Optional[str] = None) -> str:
        cfg = cls.load_config(config_path)
        engines_cfg = cfg.get("engines", {})
        if isinstance(engines_cfg, dict):
            return engines_cfg.get("selected_engine", "f5-tts")
        return "f5-tts"

    @classmethod
    def get_engine_adapter(cls, engine_name: Optional[str] = None, config_path: Optional[str] = None, **kwargs) -> BaseTTSAdapter:
        if not engine_name:
            engine_name = cls.get_selected_engine_name(config_path)
        
        engine_name = engine_name.lower().strip()
        adapter_cls = ADAPTER_REGISTRY.get(engine_name)
        if not adapter_cls:
            raise ValueError(f"Unknown engine: '{engine_name}'. Available: {list(ADAPTER_REGISTRY.keys())}")
        
        return adapter_cls(**kwargs)
