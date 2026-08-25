#!/usr/bin/env python3
"""Phase 2: Prepare Audio Pipeline
Converts raw audio to standard 24kHz Mono 16-bit PCM WAV, applies VAD/silence trimming,
slices into 3-10s segments, and organizes by style (neutral, serious, storytelling).
"""
import os
import sys
import argparse
import glob

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

STYLES = ["neutral", "serious", "storytelling"]

def prepare_dataset(project_root: str, style_filter: str = None):
    data_dir = os.path.join(project_root, "data")
    raw_dir = os.path.join(data_dir, "raw")
    voice_dir = os.path.join(data_dir, "voice")

    # Ensure target style folders exist
    for st in STYLES:
        os.makedirs(os.path.join(raw_dir, st), exist_ok=True)
        os.makedirs(os.path.join(voice_dir, st), exist_ok=True)

    print("=" * 60)
    print("LAPQUE PERSONAL TTS — AUDIO PREPARATION PIPELINE")
    print("=" * 60)
    print(f"Raw data directory   : {raw_dir}")
    print(f"Voice output directory: {voice_dir}")
    print(f"Target format        : WAV, {TARGET_SAMPLE_RATE}Hz, Mono, 16-bit PCM")
    print(f"Segment duration     : 3.0s - 10.0s")
    print("-" * 60)

    target_styles = [style_filter] if style_filter and style_filter in STYLES else STYLES

    total_raw_found = 0
    total_segments_generated = 0

    for st in target_styles:
        st_raw_dir = os.path.join(raw_dir, st)
        st_out_dir = os.path.join(voice_dir, st)

        # Collect raw audio files
        raw_files = []
        for ext in ("*.wav", "*.mp3", "*.m4a", "*.flac", "*.ogg"):
            raw_files.extend(glob.glob(os.path.join(st_raw_dir, ext)))
            raw_files.extend(glob.glob(os.path.join(st_raw_dir, ext.upper())))

        print(f"\n[Style: {st}] Found {len(raw_files)} raw audio files.")
        total_raw_found += len(raw_files)

        for idx, rfile in enumerate(raw_files):
            base_name = os.path.splitext(os.path.basename(rfile))[0]
            print(f"  -> Processing [{idx+1}/{len(raw_files)}]: {os.path.basename(rfile)}")
            try:
                # 1. Convert to normalized standard WAV
                temp_wav = os.path.join(data_dir, "processed", f"temp_{base_name}.wav")
                AudioProcessor.convert_to_wav(rfile, temp_wav, target_sr=TARGET_SAMPLE_RATE)

                # 2. Read samples
                samples, sr, _ = AudioProcessor.read_wav_pcm16(temp_wav)

                # 3. VAD & Segmenting
                segments = AudioProcessor.segment_audio(samples, sample_rate=sr, min_sec=3.0, max_sec=10.0)
                print(f"     Sliced into {len(segments)} segments (3-10s).")

                # 4. Save segments
                for s_idx, seg in enumerate(segments):
                    out_filename = f"{st}_{base_name}_seg{s_idx+1:03d}.wav"
                    out_filepath = os.path.join(st_out_dir, out_filename)
                    AudioProcessor.write_wav_pcm16(out_filepath, seg, sample_rate=sr)
                    total_segments_generated += 1

                # Clean up temp
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)

            except Exception as e:
                print(f"     [ERROR] Failed processing {rfile}: {e}")

    print("\n" + "=" * 60)
    print(f"AUDIO PREPARATION COMPLETE.")
    print(f"Total raw files processed : {total_raw_found}")
    print(f"Total segments generated   : {total_segments_generated}")
    print("=" * 60)
    return total_raw_found, total_segments_generated

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LAPQUE Audio Preprocessing")
    parser.add_argument("--style", choices=STYLES, help="Process only a specific style")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    prepare_dataset(project_root, style_filter=args.style)
