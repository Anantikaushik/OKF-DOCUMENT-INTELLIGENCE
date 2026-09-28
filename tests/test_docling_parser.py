from pathlib import Path

from app.ingestion.docling_parser import DoclingParser


def test_docling_parser_imports():
    parser = DoclingParser()

    assert parser is not None


def test_docling_parser_output_directory():

    output_dir = Path("data/processed")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    assert output_dir.exists()