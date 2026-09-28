from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class DocumentChunk:
    document_id: str
    chunk_id: str
    page_number: int
    text: str
    section: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)