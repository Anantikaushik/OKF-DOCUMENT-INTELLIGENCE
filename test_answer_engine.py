from app.qa.answer_engine import AnswerEngine


DOCUMENT_ID = "d24e34c5ea8d44898d4b967a953c4c61"


def main():

    print("=" * 60)
    print("OKF ANSWER ENGINE TEST")
    print("=" * 60)

    engine = AnswerEngine()

    try:

        result = engine.answer(
            question="What is PixelRAG?",
            document_id=DOCUMENT_ID,
            top_k=5,
        )

        # =====================================================
        # ANSWER
        # =====================================================

        print("\nANSWER")
        print("-" * 60)
        print(result["answer"])

        # =====================================================
        # SOURCES
        # =====================================================

        print("\nSOURCES")
        print("-" * 60)

        for source in result["sources"]:

            print(
                f"Page {source['page_number']} | "
                f"{source['chunk_id']}"
            )

        # =====================================================
        # TOKEN USAGE
        # =====================================================

        usage = result["usage"]

        headroom = usage["headroom"]
        groq = usage["groq"]

        print("\nTOKEN USAGE")
        print("-" * 60)

        print(
            f"Headroom tokens before : "
            f"{headroom['tokens_before']}"
        )

        print(
            f"Headroom tokens after  : "
            f"{headroom['tokens_after']}"
        )

        print(
            f"Headroom tokens saved  : "
            f"{headroom['tokens_saved']}"
        )

        print(
            f"Compression ratio      : "
            f"{headroom['compression_ratio']:.2f}"
        )

        print(
            f"Groq input tokens      : "
            f"{groq['input_tokens']}"
        )

        print(
            f"Groq output tokens     : "
            f"{groq['output_tokens']}"
        )

        print(
            f"Groq total tokens      : "
            f"{groq['total_tokens']}"
        )

        # =====================================================
        # HEADROOM TRANSFORMS
        # =====================================================

        print("\nHEADROOM TRANSFORMS")
        print("-" * 60)

        transforms = headroom["transforms_applied"]

        if transforms:

            for transform in transforms:
                print(f"- {transform}")

        else:
            print("No transformations applied.")

        # =====================================================
        # VALIDATION
        # =====================================================

        assert result["answer"]

        assert isinstance(
            result["sources"],
            list,
        )

        assert "headroom" in usage
        assert "groq" in usage

        assert (
            groq["total_tokens"]
            == groq["input_tokens"]
            + groq["output_tokens"]
        )

        print("\n" + "=" * 60)
        print("✅ Answer engine test successful.")
        print("=" * 60)

    finally:

        engine.close()


if __name__ == "__main__":
    main()