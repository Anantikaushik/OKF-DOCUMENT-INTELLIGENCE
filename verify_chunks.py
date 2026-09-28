from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


PROCESSED_DIR = Path("data/processed")


def main() -> None:

    chunk_files = list(
        PROCESSED_DIR.rglob("chunks.json")
    )

    if not chunk_files:
        raise FileNotFoundError(
            "No chunks.json found inside data/processed/"
        )

    chunks_path = chunk_files[0]

    print("=" * 70)
    print("OKF CHUNK VERIFICATION")
    print("=" * 70)
    print(f"File: {chunks_path}")
    print()

    with chunks_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    chunks = data.get("chunks", [])

    if not chunks:
        raise ValueError(
            "chunks.json contains no chunks."
        )

    print(f"Total chunks: {len(chunks)}")
    print()

    # --------------------------------------------------
    # PAGE NUMBERS
    # --------------------------------------------------

    page_numbers = [
        chunk["page_number"]
        for chunk in chunks
        if "page_number" in chunk
    ]

    unique_pages = sorted(
        set(page_numbers)
    )

    print(f"Unique pages represented: {len(unique_pages)}")

    if unique_pages:
        print(
            f"First page: {unique_pages[0]}"
        )
        print(
            f"Last page: {unique_pages[-1]}"
        )

    print()

    # --------------------------------------------------
    # CHUNKS PER PAGE
    # --------------------------------------------------

    page_counts = Counter(
        page_numbers
    )

    print("Chunks per page:")

    for page_number in unique_pages[:10]:

        print(
            f"  Page {page_number}: "
            f"{page_counts[page_number]} chunks"
        )

    if len(unique_pages) > 10:
        print("  ...")

        for page_number in unique_pages[-5:]:

            print(
                f"  Page {page_number}: "
                f"{page_counts[page_number]} chunks"
            )

    print()

    # --------------------------------------------------
    # SAMPLE CHUNKS
    # --------------------------------------------------

    print("=" * 70)
    print("SAMPLE CHUNKS")
    print("=" * 70)

    for chunk in chunks[:5]:

        print()
        print(
            f"Chunk ID: {chunk.get('chunk_id')}"
        )

        print(
            f"Page: {chunk.get('page_number')}"
        )

        text = chunk.get(
            "text",
            "",
        )

        print(
            f"Text: {text[:300]}"
        )

    print()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    missing_page = [
        chunk
        for chunk in chunks
        if not chunk.get("page_number")
    ]

    missing_text = [
        chunk
        for chunk in chunks
        if not chunk.get("text", "").strip()
    ]

    missing_id = [
        chunk
        for chunk in chunks
        if not chunk.get("chunk_id")
    ]

    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"Chunks missing page number: "
        f"{len(missing_page)}"
    )

    print(
        f"Chunks missing text: "
        f"{len(missing_text)}"
    )

    print(
        f"Chunks missing ID: "
        f"{len(missing_id)}"
    )

    print()

    if missing_page:
        raise ValueError(
            "Some chunks do not have page numbers."
        )

    if missing_text:
        raise ValueError(
            "Some chunks contain empty text."
        )

    if missing_id:
        raise ValueError(
            "Some chunks do not have chunk IDs."
        )

    print("✅ Chunk validation successful.")


if __name__ == "__main__":
    main()