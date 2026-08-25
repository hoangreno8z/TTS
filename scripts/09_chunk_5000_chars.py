#!/usr/bin/env python3
"""Phase 9: Chunk Long Text CLI (up to 5,000 characters).
Demonstrates splitting long Vietnamese text into sentence/clause-aligned chunks
without cutting words in the middle.
"""
import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.long_text_processor import LongTextProcessor
from app.text_norm import VietnameseNormalizer

def run_chunking(input_text_or_file: str, max_chars: int = 250):
    text = input_text_or_file
    if os.path.exists(input_text_or_file):
        with open(input_text_or_file, "r", encoding="utf-8") as f:
            text = f.read()

    print("=" * 60)
    print("LAPQUE PERSONAL TTS — LONG TEXT CHUNKER (~5,000 CHARACTERS)")
    print("=" * 60)
    print(f"Total Input Length: {len(text)} characters")
    print(f"Max Chunk Size    : {max_chars} characters")
    print("-" * 60)

    chunks = LongTextProcessor.split_into_chunks(text, max_chunk_chars=max_chars)
    print(f"Total Chunks Created: {len(chunks)}\n")

    for idx, c in enumerate(chunks):
        norm = VietnameseNormalizer.normalize(c)
        print(f"--- Chunk [{idx+1:02d}/{len(chunks):02d}] ({len(c)} chars) ---")
        print(f"RAW : {c}")
        print(f"NORM: {norm}\n")

    print("=" * 60)
    return chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split long text into TTS chunks")
    parser.add_argument("--text", help="Text to split")
    parser.add_argument("--file", help="File containing long text")
    parser.add_argument("--max-chars", type=int, default=250, help="Maximum characters per chunk")
    args = parser.parse_args()

    sample_long_text = (
        "Trải qua hàng ngàn năm lịch sử dựng nước và giữ nước, dân tộc Việt Nam đã hun đúc nên truyền thống "
        "yêu nước nồng nàn, tinh thần đoàn kết keo sơn và ý chí tự lực tự cường bất khuất. "
        "Mỗi giai đoạn lịch sử đều ghi dấu những chiến công hiển hách, những trang sử vàng chói lọi của cha ông ta. "
        "Ngày nay, trong kỷ nguyên số hóa và hội nhập quốc tế sâu rộng, thế hệ trẻ tiếp tục kế thừa và phát huy "
        "những giá trị cao đẹp đó, không ngừng sáng tạo, làm chủ công nghệ mới để đưa đất nước phát triển phồn vinh. "
        "Đặc biệt, việc ứng dụng trí tuệ nhân tạo và công nghệ xử lý tiếng nói tự nhiên tiếng Việt đang mở ra vô vàn "
        "cơ hội mới trong giáo dục, y tế và đời sống hàng ngày."
    )

    inp = args.text or args.file or sample_long_text
    run_chunking(inp, max_chars=args.max_chars)
