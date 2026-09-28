from __future__ import annotations

import json
from pathlib import Path

from app.okf.schema import DocumentChunk


def write_chunks(
    chunks: list[DocumentChunk],
    output_path: str | Path,
) -> Path:

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "chunk_count": len(chunks),
        "chunks": [
            chunk.to_dict()
            for chunk in chunks
        ],
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path