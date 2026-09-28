import json

from app.okf.chunker import DocumentChunker
from app.okf.writer import write_chunks


def test_docling_page_aware_chunking(tmp_path):

    docling_json = {
        "texts": [
            {
                "text": "Content from page one.",
                "prov": [
                    {
                        "page_no": 1
                    }
                ],
            },
            {
                "text": "Content from page two.",
                "prov": [
                    {
                        "page_no": 2
                    }
                ],
            },
        ],
        "pages": {
            "1": {
                "page_no": 1
            },
            "2": {
                "page_no": 2
            },
        },
    }

    json_path = (
        tmp_path / "docling.json"
    )

    json_path.write_text(
        json.dumps(docling_json),
        encoding="utf-8",
    )

    chunker = DocumentChunker()

    chunks = chunker.chunk_docling_json(
        json_path=json_path,
        document_id="testdoc",
    )

    assert len(chunks) == 2

    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2

    assert chunks[0].chunk_id == (
        "testdoc_p1_c1"
    )

    assert chunks[1].chunk_id == (
        "testdoc_p2_c1"
    )


def test_write_chunks(tmp_path):

    chunker = DocumentChunker()

    docling_json = {
        "texts": [
            {
                "text": "Test content.",
                "prov": [
                    {
                        "page_no": 3
                    }
                ],
            }
        ]
    }

    input_path = (
        tmp_path / "input.json"
    )

    input_path.write_text(
        json.dumps(docling_json),
        encoding="utf-8",
    )

    chunks = chunker.chunk_docling_json(
        input_path,
        "document123",
    )

    output_path = (
        tmp_path / "chunks.json"
    )

    write_chunks(
        chunks,
        output_path,
    )

    assert output_path.exists()

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert saved["chunk_count"] == 1
    assert (
        saved["chunks"][0]["page_number"]
        == 3
    )