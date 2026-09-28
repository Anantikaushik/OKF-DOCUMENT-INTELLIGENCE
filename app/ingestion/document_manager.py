from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pypdf import PdfReader

from app.graph.graph_entity_ingestion import ingest_entities
from app.graph.graph_ingestion import ingest_chunks
from app.ingestion.docling_parser import DoclingParser
from app.okf.chunker import DocumentChunker
from app.okf.writer import write_chunks
from app.retrieval.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
DOCUMENT_DIR = PROJECT_ROOT / "data" / "documents"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class DocumentManager:
    """Handles uploaded PDF files and their metadata."""

    @staticmethod
    def knowledge_graph_enabled() -> bool:
        """Allow graph ingestion only when explicitly enabled."""
        value = os.getenv("ENABLE_KNOWLEDGE_GRAPH_INGESTION", "false").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def validate_pdf(self, file_bytes: bytes) -> dict:
        """Validate PDF and extract basic metadata."""

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_stream)
            page_count = len(reader.pages)

        except Exception as exc:
            raise ValueError(
                f"Unable to read the PDF: {exc}"
            ) from exc

        if page_count == 0:
            raise ValueError("The PDF contains no pages.")

        return {
            "page_count": page_count,
        }

    def process_document(
        self,
        document_id: str,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict:
        """Parse, chunk, index and ingest a saved PDF document."""

        def report(message: str) -> None:
            if progress_callback is not None:
                progress_callback(message)

        metadata_path = DOCUMENT_DIR / f"{document_id}.json"

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Document metadata not found for: {document_id}"
            )

        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)

        pdf_path = Path(
            metadata.get("pdf_path", UPLOAD_DIR / f"{document_id}.pdf")
        )

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found for document {document_id}: {pdf_path}"
            )

        output_dir = PROCESSED_DIR / document_id
        report("Parsing PDF structure and text...")
        parser = DoclingParser()
        parse_result = parser.parse(
            pdf_path=pdf_path,
            output_dir=output_dir,
            document_id=document_id,
        )

        report("Splitting document into searchable chunks...")
        chunker = DocumentChunker(
            max_characters=1800,
            overlap_characters=200,
        )

        chunks = chunker.chunk_docling_json(
            json_path=parse_result["json_path"],
            document_id=document_id,
        )

        chunks_path = output_dir / "chunks.json"
        write_chunks(
            chunks=chunks,
            output_path=chunks_path,
        )

        report("Creating semantic search index (this may take a moment)...")
        index_path = output_dir / "vector_index.json"
        VectorStore().build_index(
            chunks_path=str(chunks_path),
            output_path=str(index_path),
        )

        if self.knowledge_graph_enabled():
            try:
                report("Saving document to the knowledge graph...")
                ingest_chunks(str(chunks_path))
                ingest_entities(str(chunks_path))
            except Exception as exc:
                print(f"Graph ingestion skipped for {document_id}: {exc}")
                report("Knowledge graph unavailable; continuing with search index.")
        else:
            report(
                "Knowledge graph ingestion is disabled for faster document ingest. "
                "Set ENABLE_KNOWLEDGE_GRAPH_INGESTION=true to enable it."
            )

        report("Finalizing document...")
        metadata["status"] = "processed"
        metadata["processed_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        metadata["processed_dir"] = str(output_dir)
        metadata["chunks_path"] = str(chunks_path)
        metadata["vector_index_path"] = str(index_path)

        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return metadata

    def save_document(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict:
        """Validate and persist an uploaded PDF."""

        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        validation = self.validate_pdf(file_bytes)

        document_id = uuid.uuid4().hex

        safe_filename = Path(filename).name

        pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
        metadata_path = DOCUMENT_DIR / f"{document_id}.json"

        # Save the original PDF unchanged.
        pdf_path.write_bytes(file_bytes)

        metadata = {
            "document_id": document_id,
            "filename": safe_filename,
            "page_count": validation["page_count"],
            "file_size_bytes": len(file_bytes),
            "uploaded_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "status": "uploaded",
            "pdf_path": str(pdf_path),
        }

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        return metadata