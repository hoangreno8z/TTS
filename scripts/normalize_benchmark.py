#!/usr/bin/env python3
"""Helper script to normalize benchmark sentences and preview output."""
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.text_norm import VietnameseNormalizer

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(root, "benchmark", "benchmark_sentences.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 60)
    print("VIETNAMESE TEXT NORMALIZER — 20 BENCHMARK SENTENCES PREVIEW")
    print("=" * 60)
    for s in data["sentences"]:
        raw = s["text"]
        norm = VietnameseNormalizer.normalize(raw)
        print(f"[{s['id']:02d}] ({s['category']})")
        print(f"  RAW : {raw}")
        print(f"  NORM: {norm}\n")

if __name__ == "__main__":
    main()
