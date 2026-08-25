#!/usr/bin/env python3
"""Phase 9: Export MP3 CLI.
Converts master WAV files to standard MP3 format using FFmpeg if available.
"""
import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.long_text_processor import LongTextProcessor

def run_export(wav_file: str, mp3_file: str = None, bitrate: str = "192k"):
    if not mp3_file:
        base = os.path.splitext(wav_file)[0]
        mp3_file = f"{base}.mp3"

    print("=" * 60)
    print("LAPQUE PERSONAL TTS — MP3 EXPORTER")
    print("=" * 60)
    print(f"Source WAV : {wav_file}")
    print(f"Target MP3 : {mp3_file}")
    print(f"Bitrate    : {bitrate}")
    print("-" * 60)

    res = LongTextProcessor.export_to_mp3(wav_file, mp3_file, bitrate=bitrate)
    if res:
        print(f"[SUCCESS] Exported MP3: {res}")
    else:
        print("[NOTE] MP3 export skipped (FFmpeg not available). WAV master is preserved.")
    print("=" * 60)
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export WAV to MP3")
    parser.add_argument("wav_file", help="Source WAV file path")
    parser.add_argument("--out", help="Target MP3 file path")
    parser.add_argument("--bitrate", default="192k", help="MP3 audio bitrate")
    args = parser.parse_args()

    run_export(args.wav_file, args.out, bitrate=args.bitrate)
