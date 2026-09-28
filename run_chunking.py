from __future__ import annotations

from pathlib import Path

from app.okf.chunker import DocumentChunker
from app.okf.writer import write_chunks


PROCESSED_DIR = Path("data/processed")


def main() -> None:

    json_files = list(
        PROCESSED_DIR.rglob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(
            "No Docling JSON found inside data/processed/"
        )

    # Ignore any existing chunks.json
    json_files = [
        path
        for path in json_files
        if path.name != "chunks.json"
    ]

    if not json_files:
        raise FileNotFoundError(
            "No Docling source JSON found."
        )

    json_path = json_files[0]

    document_id = json_path.stem

    output_path = (
        json_path.parent / "chunks.json"
    )

    print("=" * 70)
    print("OKF CHUNKING")
    print("=" * 70)

    print(f"Docling JSON: {json_path}")
    print(f"Document ID: {document_id}")
    print(f"Output: {output_path}")
    print()

    chunker = DocumentChunker(
        max_characters=1800,
        overlap_characters=200,
    )

    print("Creating page-aware chunks...")

    chunks = chunker.chunk_docling_json(
        json_path=json_path,
        document_id=document_id,
    )

    print(f"Chunks created: {len(chunks)}")
    print()

    write_chunks(
        chunks=chunks,
        output_path=output_path,
    )

    print("=" * 70)
    print("CHUNKING COMPLETE")
    print("=" * 70)

    print(f"Output file: {output_path}")
    print(f"Total chunks: {len(chunks)}")


if __name__ == "__main__":
    main()