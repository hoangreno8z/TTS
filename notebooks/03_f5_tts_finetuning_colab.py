"""Google Colab Reproducible Fine-Tuning Script for F5-TTS on User Voice Dataset (Free T4 GPU).
Splits dataset into 85% Train / 15% Validation and trains F5-TTS DiT model safely.
"""

# Cell 1: Install Dependencies
# !pip install --quiet torch torchaudio soundfile librosa git+https://github.com/SWivid/F5-TTS.git accelerate wandb

import os
import sys
import json
import csv
import random
import torch

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name   : {torch.cuda.get_device_name(0)}")

def prepare_dataset_splits(metadata_csv_path: str, output_dir: str = "dataset_splits"):
    os.makedirs(output_dir, exist_ok=True)
    rows = []
    with open(metadata_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("file") and r.get("text"):
                rows.append(r)

    random.seed(42)
    random.shuffle(rows)
    split_idx = int(len(rows) * 0.85)
    train_rows = rows[:split_idx]
    val_rows = rows[split_idx:]

    train_csv = os.path.join(output_dir, "train.csv")
    val_csv = os.path.join(output_dir, "val.csv")

    with open(train_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(train_rows)

    with open(val_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(val_rows)

    print(f"Dataset split complete: {len(train_rows)} train, {len(val_rows)} validation samples.")
    return train_csv, val_csv

def start_finetuning(train_csv: str, val_csv: str, epochs: int = 20, lr: float = 1e-5):
    print(f"Starting F5-TTS fine-tuning: {epochs} epochs, lr={lr}...")
    # Accelerate training command launcher
    cmd = (
        f"accelerate launch -m f5_tts.train.train "
        f"--train_dataset {train_csv} "
        f"--val_dataset {val_csv} "
        f"--learning_rate {lr} "
        f"--epochs {epochs} "
        f"--output_dir checkpoints/finetuned_f5"
    )
    print(f"Command: {cmd}")
    # os.system(cmd)

if __name__ == "__main__":
    meta_path = sys.argv[1] if len(sys.argv) > 1 else "data/metadata/metadata.csv"
    if os.path.exists(meta_path):
        tr, va = prepare_dataset_splits(meta_path)
        start_finetuning(tr, va)
    else:
        print(f"Metadata file not found at {meta_path}. Please prepare dataset in Phase 2.")
