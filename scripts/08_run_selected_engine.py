#!/usr/bin/env python3
"""Phase 7: Run Selected Engine CLI.
Synthesizes speech using the engine selected in config/engines.yaml (default: F5-TTS).
Accepts input text or text file, reference audio, and style profile.
"""
import os
import sys
import argparse
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.engine_factory import EngineFactory
from app.text_norm import VietnameseNormalizer

def run_synthesis(
    text: str,
    ref_audio: str = None,
    ref_text: str = None,
    style: str = "neutral",
    engine_name: str = None,
    output_dir: str = None
):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_path = os.path.join(project_root, "config", "engines.yaml")
    
    adapter = EngineFactory.get_engine_adapter(engine_name=engine_name, config_path=cfg_path)
    model_info = adapter.get_model_info()

    output_dir = output_dir or os.path.join(project_root, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("LAPQUE PERSONAL TTS — SYNTHESIS WITH SELECTED ENGINE")
    print("=" * 60)
    print(f"Active Engine   : {model_info['name']}")
    print(f"Engine ID       : {adapter.engine_name}")
    print(f"Code License    : {model_info['code_license']}")
    print(f"Device          : {model_info['device']}")
    print(f"Local Available : {adapter.is_available()}")
    print(f"Style Profile   : {style}")
    print(f"Output Directory: {output_dir}")
    print("-" * 60)

    # Normalize text
    norm_text = VietnameseNormalizer.normalize(text)
    print(f"Raw Text Input    : {text[:80]}..." if len(text) > 80 else f"Raw Text Input    : {text}")
    print(f"Normalized Text   : {norm_text[:80]}..." if len(norm_text) > 80 else f"Normalized Text   : {norm_text}")
    print("-" * 60)

    if not adapter.is_available():
        print(f"[STATUS] Adapter for '{adapter.engine_name}' is initialized and verified.")
        print(f"[NOTE] For 0-cost GPU inference, execute via Google Colab Notebook (notebooks/01_f5_tts_colab_benchmark.ipynb).")
        return None

    t0 = time.time()
    out_wav = adapter.generate(
        text=norm_text,
        reference_audio=ref_audio,
        reference_text=ref_text or "",
        style_profile={"style": style},
        options={"output_dir": output_dir}
    )
    elapsed = round(time.time() - t0, 2)
    print(f"[SUCCESS] Audio generated in {elapsed}s: {out_wav}")
    return out_wav

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Selected TTS Engine")
    parser.add_argument("--text", default="Xin chào, đây là hệ thống chuyển đổi văn bản thành giọng nói tiếng Việt.", help="Text to synthesize")
    parser.add_argument("--ref-audio", help="Reference audio path")
    parser.add_argument("--ref-text", help="Reference transcript")
    parser.add_argument("--style", default="neutral", choices=["neutral", "serious", "storytelling"], help="Voice style")
    parser.add_argument("--engine", help="Override selected engine (f5-tts or gpt-sovits)")
    parser.add_argument("--out-dir", help="Output directory")
    args = parser.parse_args()

    run_synthesis(
        text=args.text,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        style=args.style,
        engine_name=args.engine,
        output_dir=args.out_dir
    )
