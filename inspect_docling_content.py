from __future__ import annotations

import json
from pathlib import Path


PROCESSED_DIR = Path("data/processed")


def main():

    json_files = [
        p
        for p in PROCESSED_DIR.rglob("*.json")
        if p.name != "chunks.json"
    ]

    if not json_files:
        raise FileNotFoundError(
            "No Docling JSON found."
        )

    json_path = json_files[0]

    with json_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    print("=" * 70)
    print("DEEP DOCLING CONTENT INSPECTION")
    print("=" * 70)

    print(f"JSON: {json_path}")
    print()

    # --------------------------------------------------
    # PAGES
    # --------------------------------------------------

    pages = data.get("pages", {})

    print("TOTAL DOCLING PAGES:", len(pages))
    print()

    print("PAGE NUMBERS:")

    for key, page in pages.items():

        print(
            f"  key={key} "
            f"page_no={page.get('page_no')} "
            f"keys={list(page.keys())}"
        )

    # --------------------------------------------------
    # TEXTS
    # --------------------------------------------------

    texts = data.get("texts", [])

    print()
    print("=" * 70)
    print("TEXT ITEMS")
    print("=" * 70)

    print("Total text items:", len(texts))
    print()

    for index, item in enumerate(texts):

        print(f"TEXT ITEM {index}")

        print(
            "Keys:",
            list(item.keys())
        )

        print(
            "Text:",
            repr(
                item.get("text", "")
            )[:500]
        )

        print(
            "Label:",
            item.get("label")
        )

        print(
            "Prov:",
            item.get("prov")
        )

        print("-" * 70)

    # --------------------------------------------------
    # BODY
    # --------------------------------------------------

    body = data.get("body", {})

    print()
    print("=" * 70)
    print("BODY")
    print("=" * 70)

    print(
        json.dumps(
            body,
            indent=2,
            ensure_ascii=False,
        )[:10000]
    )

    # --------------------------------------------------
    # GROUPS
    # --------------------------------------------------

    groups = data.get("groups", [])

    print()
    print("=" * 70)
    print("GROUPS")
    print("=" * 70)

    print(
        "Total groups:",
        len(groups)
    )

    for index, group in enumerate(groups):

        print()
        print(
            f"GROUP {index}"
        )

        print(
            json.dumps(
                group,
                indent=2,
                ensure_ascii=False,
            )[:5000]
        )

    print()
    print("=" * 70)
    print("END")
    print("=" * 70)


if __name__ == "__main__":
    main()