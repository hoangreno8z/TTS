"""Long-Text Processing & Audio Stitching Engine for LAPQUE Vietnamese TTS.
Handles up to 5,000 characters per request:
1. Sentence-aware chunking without breaking words.
2. Sequential chunk synthesis.
3. High-fidelity WAV merging with smooth silence pauses and cross-fades.
4. Optional MP3 export via FFmpeg.
"""
import os
import sys
import re
import math
import struct
import wave
import shutil
import subprocess
from typing import List, Dict, Tuple, Optional, Any

from .text_norm import VietnameseNormalizer
from .audio_processing import AudioProcessor, TARGET_SAMPLE_RATE

class LongTextProcessor:
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into raw sentences by punctuation boundaries (. ? ! newline)."""
        if not text:
            return []
        
        # Normalize carriage returns
        t = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Regex split on sentence boundaries (. ? ! \n)
        # Keeps sentence delimiters
        raw_parts = re.split(r"([\.\?!]+[\s\n]+|\n{2,})", t)
        
        sentences = []
        cur = ""
        for p in raw_parts:
            if re.match(r"^([\.\?!]+[\s\n]+|\n{2,})$", p):
                cur += p.strip()
                if cur.strip():
                    sentences.append(cur.strip())
                cur = ""
            else:
                cur += p
        if cur.strip():
            sentences.append(cur.strip())
        
        return [s for s in sentences if s.strip()]

    @classmethod
    def split_into_chunks(
        cls,
        text: str,
        max_chunk_chars: int = 250,
        min_chunk_chars: int = 40
    ) -> List[str]:
        """Splits text up to 5,000 characters into optimal chunks for TTS synthesis.
        Guarantees:
        - Never splits in the middle of a word.
        - Preserves sentence order.
        - Respects punctuation pauses (, ; : -).
        """
        if not text:
            return []
        
        sentences = cls.split_into_sentences(text)
        if not sentences:
            # Fallback if no punctuation
            sentences = [text.strip()]

        chunks = []
        cur_chunk = ""

        for sent in sentences:
            # If sentence itself exceeds max_chunk_chars, split by commas/semicolons/clauses
            if len(sent) > max_chunk_chars:
                clauses = re.split(r"([,;:\—\–\-])\s*", sent)
                clause_accum = ""
                for cl in clauses:
                    if len(clause_accum) + len(cl) <= max_chunk_chars:
                        clause_accum += cl
                    else:
                        if clause_accum.strip():
                            if cur_chunk:
                                chunks.append(cur_chunk.strip())
                                cur_chunk = ""
                            chunks.append(clause_accum.strip())
                        clause_accum = cl
                if clause_accum.strip():
                    if len(cur_chunk) + len(clause_accum) + 1 <= max_chunk_chars:
                        cur_chunk = f"{cur_chunk} {clause_accum}".strip()
                    else:
                        if cur_chunk:
                            chunks.append(cur_chunk.strip())
                        cur_chunk = clause_accum.strip()
            else:
                # Normal sentence accumulation
                if not cur_chunk:
                    cur_chunk = sent
                elif len(cur_chunk) + len(sent) + 1 <= max_chunk_chars:
                    cur_chunk = f"{cur_chunk} {sent}"
                else:
                    chunks.append(cur_chunk.strip())
                    cur_chunk = sent

        if cur_chunk.strip():
            chunks.append(cur_chunk.strip())

        return chunks

    @classmethod
    def merge_wav_files(
        cls,
        wav_paths: List[str],
        output_path: str,
        pause_ms: int = 250,
        sample_rate: int = TARGET_SAMPLE_RATE
    ) -> str:
        """Merges multiple 16-bit PCM WAV chunks sequentially into a single WAV file,
        inserting natural silence pauses between chunks.
        """
        if not wav_paths:
            raise ValueError("No WAV files provided for merging.")
        
        if len(wav_paths) == 1:
            shutil.copyfile(wav_paths[0], output_path)
            return output_path

        merged_samples: List[int] = []
        pause_sample_count = int(sample_rate * (pause_ms / 1000.0))
        silence_padding = [0] * pause_sample_count

        for idx, wpath in enumerate(wav_paths):
            if not os.path.exists(wpath):
                continue
            samples, sr, _ = AudioProcessor.read_wav_pcm16(wpath)
            if sr != sample_rate:
                samples = AudioProcessor.resample_linear(samples, sr, sample_rate)

            # Apply smooth 5ms fade-in/fade-out at chunk borders to prevent clicks
            fade_len = min(int(sample_rate * 0.005), len(samples) // 4)
            if fade_len > 0:
                for i in range(fade_len):
                    gain = i / float(fade_len)
                    samples[i] = int(samples[i] * gain)
                    samples[-1 - i] = int(samples[-1 - i] * gain)

            merged_samples.extend(samples)
            if idx < len(wav_paths) - 1:
                merged_samples.extend(silence_padding)

        AudioProcessor.write_wav_pcm16(output_path, merged_samples, sample_rate=sample_rate)
        return output_path

    @staticmethod
    def export_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "192k") -> Optional[str]:
        """Convert a master WAV file to MP3 using FFmpeg if installed."""
        if not shutil.which("ffmpeg"):
            print("FFmpeg is not available in PATH. Skipping MP3 export.")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(mp3_path)), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-i", wav_path,
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            mp3_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return mp3_path
        else:
            print(f"FFmpeg MP3 export failed: {res.stderr}")
            return None
