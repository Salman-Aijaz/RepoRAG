"""
✂️ File Loading & Text Chunking
"""

from pathlib import Path
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, MAX_FILE_SIZE


def load_and_chunk_files(files: List[str]) -> List[Dict]:
    """Read files, split into overlapping chunks, return list of dicts."""
    print("📄 Loading and chunking files...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\nclass ", "\ndef ", "\nfunction ", "\n", " "],
    )

    chunks: List[Dict] = []

    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                continue

            if len(content) > MAX_FILE_SIZE:
                print(f"⚠️  Skipped large file (>{MAX_FILE_SIZE // 1000}KB): {Path(file).name}")
                continue

            for chunk in splitter.split_text(content):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "file":     file,
                        "filename": Path(file).name,
                        "rel_path": str(Path(file)),
                    },
                })

        except Exception as e:
            print(f"⚠️  Skipped {file}: {e}")

    print(f"✅ Created {len(chunks)} chunks")
    return chunks