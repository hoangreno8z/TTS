#!/usr/bin/env python3
"""Phase 2: Audio Transcription Utility (ASR Draft & Verification)
Transcribes audio segments into draft Vietnamese transcripts using OpenAI Whisper / Faster-Whisper if available,
or generates human-editable transcript templates for verification.
Rules: Never modify transcripts with LLM without explicit user verification.
"""
import os
import sys
import glob
import json
import argparse

STYLES = ["neutral", "serious", "storytelling"]

def transcribe_segments(project_root: str, language: str = "vi", model_size: str = "base"):
    voice_dir = os.path.join(project_root, "data", "voice")
    meta_dir = os.path.join(project_root, "data", "metadata")
    os.makedirs(meta_dir, exist_ok=True)

    output_draft_json = os.path.join(meta_dir, "draft_transcripts.json")

    # Try importing whisper
    whisper_module = None
    try:
        import whisper
        whisper_module = whisper
        print(f"-> OpenAI Whisper detected. Loading '{model_size}' model for Vietnamese ASR...")
        model = whisper.load_model(model_size)
    except ImportError:
        try:
            from faster_whisper import WhisperModel
            print(f"-> faster-whisper detected. Loading '{model_size}' model for Vietnamese ASR...")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            whisper_module = "faster_whisper"
        except ImportError:
            print("-> Note: Whisper not installed locally. Generating template draft for manual entry.")
            whisper_module = None

    transcripts = {}
    if os.path.exists(output_draft_json):
        try:
            with open(output_draft_json, "r", encoding="utf-8") as f:
                transcripts = json.load(f)
        except Exception:
            transcripts = {}

    total_segments = 0
    new_transcribed = 0

    for st in STYLES:
        st_dir = os.path.join(voice_dir, st)
        if not os.path.exists(st_dir):
            continue

        wavs = glob.glob(os.path.join(st_dir, "*.wav"))
        for wav_path in wavs:
            total_segments += 1
            rel_path = os.path.relpath(wav_path, project_root).replace("\\", "/")
            
            if rel_path in transcripts and transcripts[rel_path].get("text"):
                continue  # Already transcribed / reviewed

            draft_text = ""
            if whisper_module == "faster_whisper":
                try:
                    segments, _ = model.transcribe(wav_path, language=language)
                    draft_text = " ".join([s.text.strip() for s in segments])
                except Exception as e:
                    print(f"  [ASR Error] {os.path.basename(wav_path)}: {e}")
            elif whisper_module is not None:
                try:
                    res = model.transcribe(wav_path, language=language)
                    draft_text = res.get("text", "").strip()
                except Exception as e:
                    print(f"  [ASR Error] {os.path.basename(wav_path)}: {e}")

            transcripts[rel_path] = {
                "filename": os.path.basename(wav_path),
                "style": st,
                "text": draft_text,
                "status": "asr_draft" if draft_text else "needs_transcript",
                "verified": False
            }
            new_transcribed += 1

    with open(output_draft_json, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("TRANSCRIPTION PIPELINE STATUS")
    print("=" * 60)
    print(f"Total segments found : {total_segments}")
    print(f"Drafts generated     : {new_transcribed}")
    print(f"Transcript draft saved to: {output_draft_json}")
    print("Remember: Transcripts must be verified for Vietnamese tones, numbers, and proper names.")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LAPQUE Transcription Pipeline")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    transcribe_segments(project_root, model_size=args.model)
