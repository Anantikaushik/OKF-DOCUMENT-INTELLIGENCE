from __future__ import annotations

import json
import os
from pathlib import Path

from pypdf import PdfReader
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    RapidOcrOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption


class DoclingParser:
    """Parse PDF documents using Docling."""

    def __init__(self) -> None:
        self.fast_mode = _env_bool("FAST_DOCUMENT_INGESTION", True)
        self.converter = self._create_converter(
            do_ocr=False,
            fast_mode=self.fast_mode,
        )

    @staticmethod
    def _create_converter(
        do_ocr: bool,
        fast_mode: bool,
    ) -> DocumentConverter:
        batch_size = _env_int("DOCLING_BATCH_SIZE", 4, minimum=1)
        pipeline_options = PdfPipelineOptions(
            do_ocr=do_ocr,
            do_table_structure=not fast_mode,
            force_backend_text=fast_mode and not do_ocr,
            ocr_options=RapidOcrOptions(
                lang=["english"],
                backend="onnxruntime",
            ),
            ocr_batch_size=batch_size,
            layout_batch_size=batch_size,
            table_batch_size=batch_size,
            images_scale=0.5,
        )
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                )
            }
        )

    @staticmethod
    def _requires_ocr(pdf_path: Path) -> bool:
        """Use OCR for scanned documents, not isolated blank/image pages."""
        reader = PdfReader(str(pdf_path))
        pages = list(reader.pages)
        if not pages:
            return False

        text_pages = sum(
            bool((page.extract_text() or "").strip())
            for page in pages
        )
        text_ratio = text_pages / len(pages)
        minimum_text_ratio = _env_float(
            "OCR_MIN_TEXT_PAGE_RATIO",
            default=0.5,
            minimum=0.0,
            maximum=1.0,
        )
        return text_ratio < minimum_text_ratio

    def parse(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        document_id: str,
    ) -> dict:

        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Starting PDF parsing: {pdf_path.name}")

        requires_ocr = self._requires_ocr(pdf_path)
        if self.fast_mode and not requires_ocr and _env_bool(
            "FAST_NATIVE_PDF_EXTRACTION",
            True,
        ):
            print("Embedded text detected; using native fast extraction.")
            return self._parse_native_text(
                pdf_path=pdf_path,
                output_dir=output_dir,
                document_id=document_id,
            )

        if requires_ocr:
            # OCR remains enabled for scanned PDFs, but uses the same configurable
            # batching as the native-text path.
            self.converter = self._create_converter(
                do_ocr=True,
                fast_mode=self.fast_mode,
            )
            print("Most pages have no embedded text; OCR enabled.")
        else:
            mode = "fast native-text mode" if self.fast_mode else "full layout mode"
            print(f"Embedded text detected; OCR skipped ({mode}).")

        result = self.converter.convert(
            str(pdf_path)
        )

        document = result.document

        # Export Docling's structured representation.
        markdown = document.export_to_markdown()

        markdown_path = (
            output_dir /
            f"{document_id}.md"
        )

        markdown_path.write_text(
            markdown,
            encoding="utf-8",
        )

        # Export Docling document as JSON.
        json_path = (
            output_dir /
            f"{document_id}.json"
        )

        docling_json = document.export_to_dict()

        json_path.write_text(
            json.dumps(
                docling_json,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return {
            "document_id": document_id,
            "pdf_path": str(pdf_path),
            "markdown_path": str(markdown_path),
            "json_path": str(json_path),
            "status": "parsed",
        }

    @staticmethod
    def _parse_native_text(
        pdf_path: Path,
        output_dir: Path,
        document_id: str,
    ) -> dict:
        reader = PdfReader(str(pdf_path))
        texts = []
        markdown_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            texts.append(
                {
                    "text": text,
                    "prov": [{"page_no": page_number}],
                }
            )
            markdown_pages.append(f"## Page {page_number}\n\n{text}")

        markdown_path = output_dir / f"{document_id}.md"
        markdown_path.write_text(
            "\n\n".join(markdown_pages),
            encoding="utf-8",
        )

        json_path = output_dir / f"{document_id}.json"
        json_path.write_text(
            json.dumps(
                {"texts": texts},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return {
            "document_id": document_id,
            "pdf_path": str(pdf_path),
            "markdown_path": str(markdown_path),
            "json_path": str(json_path),
            "status": "parsed",
        }


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        return max(int(os.getenv(name, str(default))), minimum)
    except ValueError:
        return default


def _env_float(
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    try:
        return min(
            max(float(os.getenv(name, str(default))), minimum),
            maximum,
        )
    except ValueError:
        return default