from __future__ import annotations

import json
from pathlib import Path

from app.okf.schema import DocumentChunk


class DocumentChunker:
    """
    Create page-aware chunks directly from Docling JSON.

    Page numbers are obtained from:
        texts[*].prov[*].page_no
    """

    def __init__(
        self,
        max_characters: int = 1800,
        overlap_characters: int = 200,
    ) -> None:

        if max_characters <= overlap_characters:
            raise ValueError(
                "max_characters must be greater than "
                "overlap_characters."
            )

        self.max_characters = max_characters
        self.overlap_characters = overlap_characters

    def chunk_docling_json(
        self,
        json_path: str | Path,
        document_id: str,
    ) -> list[DocumentChunk]:

        json_path = Path(json_path)

        if not json_path.exists():
            raise FileNotFoundError(
                f"Docling JSON not found: {json_path}"
            )

        with json_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        texts = data.get("texts", [])

        if not texts:
            return []

        page_contents: dict[int, list[str]] = {}

        for item in texts:

            text = self._extract_text(item)

            if not text.strip():
                continue

            page_numbers = self._extract_page_numbers(
                item
            )

            if not page_numbers:
                continue

            for page_number in page_numbers:

                page_contents.setdefault(
                    page_number,
                    [],
                ).append(text.strip())

        chunks: list[DocumentChunk] = []

        for page_number in sorted(page_contents):

            page_text = "\n\n".join(
                page_contents[page_number]
            )

            page_chunks = self._split_text(
                page_text
            )

            for chunk_index, chunk_text in enumerate(
                page_chunks,
                start=1,
            ):

                chunk_id = (
                    f"{document_id}"
                    f"_p{page_number}"
                    f"_c{chunk_index}"
                )

                chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        page_number=page_number,
                        text=chunk_text,
                    )
                )

        return chunks

    @staticmethod
    def _extract_text(item: dict) -> str:

        # Docling text items normally expose their
        # textual content through "text".

        text = item.get("text")

        if isinstance(text, str):
            return text

        # Defensive fallback for possible variants.
        for key in (
            "orig",
            "content",
            "value",
        ):

            value = item.get(key)

            if isinstance(value, str):
                return value

        return ""

    @staticmethod
    def _extract_page_numbers(
        item: dict,
    ) -> list[int]:

        page_numbers: list[int] = []

        provenance = item.get("prov", [])

        if not isinstance(provenance, list):
            return page_numbers

        for prov in provenance:

            if not isinstance(prov, dict):
                continue

            page_number = prov.get("page_no")

            if isinstance(page_number, int):
                page_numbers.append(
                    page_number
                )

        return sorted(
            set(page_numbers)
        )

    def _split_text(
        self,
        text: str,
    ) -> list[str]:

        text = text.strip()

        if not text:
            return []

        if len(text) <= self.max_characters:
            return [text]

        chunks: list[str] = []

        start = 0
        text_length = len(text)

        while start < text_length:

            end = min(
                start + self.max_characters,
                text_length,
            )

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = (
                end -
                self.overlap_characters
            )

        return chunks