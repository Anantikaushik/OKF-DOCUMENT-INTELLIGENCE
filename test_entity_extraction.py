import json

from app.graph.entity_extractor import EntityExtractor


def main():

    print("=" * 60)
    print("ENTITY EXTRACTION TEST")
    print("=" * 60)

    text = """
    PixelRAG is a multimodal retrieval system.
    FAISS is used for vector retrieval.
    Qwen3-VL-Embedding-2B produces embeddings.
    """

    extractor = EntityExtractor()

    result = extractor.extract(text)

    print(json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    ))

    print()
    print("✅ Entity extraction successful.")


if __name__ == "__main__":
    main()