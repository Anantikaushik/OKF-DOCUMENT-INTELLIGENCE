from pathlib import Path

from app.okf.chunker import DocumentChunker


def test_chunker_initializes():

    chunker = DocumentChunker()

    assert chunker.max_characters == 1800
    assert chunker.overlap_characters == 200


def test_chunker_rejects_invalid_configuration():

    try:
        DocumentChunker(
            max_characters=100,
            overlap_characters=100,
        )

        assert False

    except ValueError:
        assert True


def test_chunk_markdown_file(tmp_path):

    markdown_file = (
        tmp_path / "test.md"
    )

    markdown_file.write_text(
        "This is test document content.",
        encoding="utf-8",
    )

    chunker = DocumentChunker()

    chunks = chunker.chunk_markdown(
        markdown_path=markdown_file,
        document_id="test123",
    )

    assert len(chunks) == 1

    assert chunks[0].document_id == "test123"
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_id.startswith(
        "test123_p1_"
    )