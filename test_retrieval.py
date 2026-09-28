from app.retrieval.retriever import GraphRetriever


DOCUMENT_ID = "d24e34c5ea8d44898d4b967a953c4c61"


def main():

    print("=" * 60)
    print("SEMANTIC RETRIEVAL TEST")
    print("=" * 60)

    retriever = GraphRetriever()

    try:

        results = retriever.retrieve(
            query="What is PixelRAG?",
            document_id=DOCUMENT_ID,
            top_k=3,
        )

        print(f"Results: {len(results)}")
        print()

        for result in results:

            print(
                f"Page       : "
                f"{result['page_number']}"
            )

            print(
                f"Similarity : "
                f"{result['similarity']:.4f}"
            )

            print(
                f"Chunk      : "
                f"{result['chunk_id']}"
            )

            print(
                f"Entities   : "
                f"{result['entities']}"
            )

            print(
                f"Text       : "
                f"{result['text'][:250]}"
            )

            print("-" * 60)

        print("✅ Semantic retrieval successful.")

    finally:
        retriever.close()


if __name__ == "__main__":
    main()