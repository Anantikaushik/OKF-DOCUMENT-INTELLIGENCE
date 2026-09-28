from __future__ import annotations

import json
from pathlib import Path


PROCESSED_DIR = Path("data/processed")


def main() -> None:

    json_files = list(
        PROCESSED_DIR.rglob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(
            "No Docling JSON file found inside data/processed/"
        )

    # Ignore metadata JSON files if any exist.
    json_files = [
        path
        for path in json_files
        if path.name != "metadata.json"
    ]

    if not json_files:
        raise FileNotFoundError(
            "No Docling document JSON found."
        )

    json_path = json_files[0]

    print("=" * 70)
    print("DOCLING JSON INSPECTION")
    print("=" * 70)
    print(f"File: {json_path}")
    print()

    with json_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    print("Top-level keys:")
    print(list(data.keys()))
    print()

    print("Top-level structure:")
    for key, value in data.items():

        if isinstance(value, dict):
            print(
                f"  {key}: dict "
                f"({len(value)} keys)"
            )

        elif isinstance(value, list):
            print(
                f"  {key}: list "
                f"({len(value)} items)"
            )

        else:
            print(
                f"  {key}: {type(value).__name__}"
            )

    print()
    print("=" * 70)
    print("SEARCHING FOR PAGE-RELATED STRUCTURES")
    print("=" * 70)

    page_keywords = {
        "page",
        "pages",
        "page_no",
        "page_number",
        "page_no",
        "provenance",
        "prov",
    }

    def inspect_structure(
        value,
        path="root",
        depth=0,
        max_depth=5,
    ):

        if depth > max_depth:
            return

        if isinstance(value, dict):

            for key, child in value.items():

                key_lower = str(key).lower()

                if any(
                    keyword in key_lower
                    for keyword in page_keywords
                ):

                    print(
                        f"{path}.{key} "
                        f"-> {type(child).__name__}"
                    )

                    if isinstance(child, list):
                        print(
                            f"    list length: "
                            f"{len(child)}"
                        )

                        if child:
                            print(
                                "    first item:"
                            )
                            print(
                                json.dumps(
                                    child[0],
                                    indent=2,
                                    ensure_ascii=False,
                                )[:2000]
                            )

                    elif isinstance(child, dict):
                        print(
                            "    keys:",
                            list(child.keys())[:30],
                        )

                    else:
                        print(
                            f"    value: {child}"
                        )

                inspect_structure(
                    child,
                    f"{path}.{key}",
                    depth + 1,
                    max_depth,
                )

        elif isinstance(value, list):

            for index, child in enumerate(
                value[:10]
            ):

                inspect_structure(
                    child,
                    f"{path}[{index}]",
                    depth + 1,
                    max_depth,
                )

    inspect_structure(data)

    print()
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()