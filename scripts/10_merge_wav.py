#!/usr/bin/env python3
"""Phase 9: Merge WAV Chunks CLI.
Merges a sequence of audio chunk WAV files into a single master WAV file,
adding natural silence padding and border anti-click cross-fading.
"""
import os
import sys
import glob
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.long_text_processor import LongTextProcessor

def run_merging(wav_files: list, output_wav: str, pause_ms: int = 250):
    print("=" * 60)
    print("LAPQUE PERSONAL TTS — WAV CHUNKS MERGER")
    print("=" * 60)
    print(f"Total Chunks to Merge: {len(wav_files)}")
    print(f"Inter-chunk Pause    : {pause_ms} ms")
    print(f"Output Master WAV    : {output_wav}")
    print("-" * 60)

    for i, w in enumerate(wav_files):
        print(f"  [{i+1:02d}/{len(wav_files):02d}] {os.path.basename(w)}")

    res = LongTextProcessor.merge_wav_files(wav_files, output_wav, pause_ms=pause_ms)
    print("-" * 60)
    print(f"[SUCCESS] Master audio file merged successfully: {res}")
    print("=" * 60)
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge WAV chunks into master audio")
    parser.add_argument("wav_files", nargs="*", help="List of WAV chunk files to merge")
    parser.add_argument("--pattern", help="Glob pattern for WAV files (e.g. 'outputs/chunk_*.wav')")
    parser.add_argument("--out", default="outputs/master_merged.wav", help="Output WAV path")
    parser.add_argument("--pause-ms", type=int, default=250, help="Pause duration between chunks in ms")
    args = parser.parse_args()

    files = args.wav_files
    if not files and args.pattern:
        files = sorted(glob.glob(args.pattern))

    if not files:
        print("Please provide at least one WAV file to merge or use --pattern.")
        sys.exit(1)

    run_merging(files, args.out, pause_ms=args.pause_ms)
