from pathlib import Path

from pypdf import PdfReader


UPLOAD_DIR = Path("data/uploads")


def main():
    pdf_files = list(UPLOAD_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            "No PDF found in data/uploads/"
        )

    for pdf_path in pdf_files:

        print("=" * 70)
        print(f"PDF: {pdf_path.name}")
        print("=" * 70)

        reader = PdfReader(str(pdf_path))

        print(
            f"Physical PDF page count: "
            f"{len(reader.pages)}"
        )

        print()


if __name__ == "__main__":
    main()