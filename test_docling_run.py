from pathlib import Path

from app.ingestion.docling_parser import DoclingParser


UPLOAD_DIR = Path("data/uploads")
PROCESSED_DIR = Path("data/processed")


def main():

    pdf_files = list(
        UPLOAD_DIR.glob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            "No PDF found in data/uploads/"
        )

    if len(pdf_files) > 1:
        print(
            f"Found {len(pdf_files)} PDFs."
        )

    pdf_path = pdf_files[0]

    document_id = pdf_path.stem

    output_dir = (
        PROCESSED_DIR /
        document_id
    )

    print("=" * 60)
    print("DOCLING TEST")
    print("=" * 60)

    print(f"PDF: {pdf_path}")
    print(f"Document ID: {document_id}")
    print(f"Output: {output_dir}")
    print()

    parser = DoclingParser()

    result = parser.parse(
        pdf_path=pdf_path,
        output_dir=output_dir,
        document_id=document_id,
    )

    print()
    print("=" * 60)
    print("DOCLING COMPLETE")
    print("=" * 60)

    print(f"Status: {result['status']}")
    print(f"Markdown: {result['markdown_path']}")
    print(f"JSON: {result['json_path']}")


if __name__ == "__main__":
    main()