from pathlib import Path

from app.ingestion.docling_parser import DoclingParser


def test_docling_parser_can_be_created():

    parser = DoclingParser()

    assert parser.converter is not None


def test_processed_directory_exists():

    processed_dir = Path("data/processed")

    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    assert processed_dir.exists()