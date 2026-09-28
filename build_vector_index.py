from app.retrieval.vector_store import VectorStore


DOCUMENT_ID = "d24e34c5ea8d44898d4b967a953c4c61"

chunks_path = (
    f"data/processed/{DOCUMENT_ID}/chunks.json"
)

index_path = (
    f"data/processed/{DOCUMENT_ID}/vector_index.json"
)


def main():

    print("=" * 60)
    print("OKF VECTOR INDEX")
    print("=" * 60)

    store = VectorStore()

    store.build_index(
        chunks_path=chunks_path,
        output_path=index_path,
    )

    print("=" * 60)
    print("VECTOR INDEX COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()