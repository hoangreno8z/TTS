#!/usr/bin/env python3
"""Phase 2: Build Metadata Dataset Index
Scans all processed audio segments, associates transcripts, measures duration and sample rate,
and outputs dataset_index.json and metadata.csv for training / zero-shot reference.
"""
import os
import sys
import glob
import json
import csv
import wave

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.audio_processing import AudioProcessor

STYLES = ["neutral", "serious", "storytelling"]

def build_metadata(project_root: str, speaker_id: str = "default_speaker"):
    voice_dir = os.path.join(project_root, "data", "voice")
    meta_dir = os.path.join(project_root, "data", "metadata")
    os.makedirs(meta_dir, exist_ok=True)

    draft_transcripts_path = os.path.join(meta_dir, "draft_transcripts.json")
    transcripts = {}
    if os.path.exists(draft_transcripts_path):
        try:
            with open(draft_transcripts_path, "r", encoding="utf-8") as f:
                transcripts = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read {draft_transcripts_path}: {e}")

    records = []
    total_duration_sec = 0.0

    for st in STYLES:
        st_dir = os.path.join(voice_dir, st)
        if not os.path.exists(st_dir):
            continue

        wav_files = sorted(glob.glob(os.path.join(st_dir, "*.wav")))
        for wpath in wav_files:
            rel_path = os.path.relpath(wpath, project_root).replace("\\", "/")
            
            # Read audio info
            duration = 0.0
            sr = 24000
            try:
                with wave.open(wpath, "rb") as wf:
                    sr = wf.getframerate()
                    frames = wf.getnframes()
                    duration = round(frames / float(sr), 3)
            except Exception as e:
                print(f"Error reading WAV info {wpath}: {e}")

            text = ""
            if rel_path in transcripts:
                text = transcripts[rel_path].get("text", "")

            # Quality heuristic based on duration
            quality_score = 1.0
            if duration < 2.0 or duration > 15.0:
                quality_score = 0.6
            elif 3.0 <= duration <= 10.0:
                quality_score = 1.0
            else:
                quality_score = 0.8

            record = {
                "file": rel_path,
                "filename": os.path.basename(wpath),
                "speaker": speaker_id,
                "style": st,
                "text": text,
                "duration_seconds": duration,
                "sample_rate": sr,
                "quality_score": quality_score
            }
            records.append(record)
            total_duration_sec += duration

    # 1. Write JSON
    json_path = os.path.join(meta_dir, "dataset_index.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "speaker": speaker_id,
            "total_segments": len(records),
            "total_duration_minutes": round(total_duration_sec / 60.0, 2),
            "segments": records
        }, f, indent=2, ensure_ascii=False)

    # 2. Write CSV
    csv_path = os.path.join(meta_dir, "metadata.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "text", "speaker", "style", "duration_seconds", "sample_rate", "quality_score"])
        for r in records:
            writer.writerow([r["file"], r["text"], r["speaker"], r["style"], r["duration_seconds"], r["sample_rate"], r["quality_score"]])

    print("=" * 60)
    print("LAPQUE DATASET METADATA BUILD COMPLETE")
    print("=" * 60)
    print(f"Total audio segments : {len(records)}")
    print(f"Total duration       : {round(total_duration_sec / 60.0, 2)} minutes ({round(total_duration_sec, 1)} seconds)")
    print(f"JSON Metadata saved  : {json_path}")
    print(f"CSV Metadata saved   : {csv_path}")
    print("=" * 60)
    return len(records), total_duration_sec

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    build_metadata(project_root)
