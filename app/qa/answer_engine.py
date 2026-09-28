from __future__ import annotations

from app.llm.groq_client import GroqClient
from app.retrieval.retriever import GraphRetriever


SYSTEM_PROMPT = """
You are a document question-answering system.

Answer the user's question ONLY using the supplied document context.

Rules:

1. Do not use outside knowledge.
2. If the answer is not supported by the context, say:
   "I could not find enough information in the document."
3. Keep the answer concise and factual.
4. Every factual statement must have a page citation.
5. Use citations exactly in this format:
   [Page X]
6. Only cite pages that appear in the supplied context.
7. Do not invent page numbers.
"""


class AnswerEngine:

    def __init__(self):
        self.groq = GroqClient()
        self.retriever = GraphRetriever()

    def answer(
        self,
        question: str,
        document_id: str,
        top_k: int = 5,
    ) -> dict:

        # =========================================================
        # RETRIEVAL
        # =========================================================

        try:
            results = self.retriever.retrieve(
                query=question,
                document_id=document_id,
                top_k=top_k,
            )
        except FileNotFoundError:
            results = []

        if not results:
            return {
                "answer": (
                    "I could not find enough information "
                    "in the document."
                ),
                "sources": [],
                "usage": {
                    "headroom": {
                        "tokens_before": 0,
                        "tokens_after": 0,
                        "tokens_saved": 0,
                        "compression_ratio": 1.0,
                        "transforms_applied": [],
                    },
                    "groq": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    },
                },
            }

        # =========================================================
        # BUILD PAGE-AWARE CONTEXT
        # =========================================================

        context_parts = []

        for result in results:

            context_parts.append(
                f"""
[Page {result['page_number']}]
Chunk ID: {result['chunk_id']}

{result['text']}
"""
            )

        context = "\n".join(context_parts)

        user_prompt = f"""
DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}

Answer the question using only the document context.
Include [Page X] citations for every factual statement.
"""

        # =========================================================
        # GROQ + HEADROOM
        # =========================================================

        response = self.groq.chat(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        answer = response.choices[0].message.content

        # =========================================================
        # TOKEN METRICS
        # =========================================================

        metrics = getattr(
            response,
            "_okf_metrics",
            {},
        )

        headroom_metrics = metrics.get(
            "headroom",
            {},
        )

        groq_metrics = metrics.get(
            "groq",
            {},
        )

        # =========================================================
        # SOURCES
        # =========================================================

        sources = []

        seen_pages = set()

        for result in results:

            page = int(result["page_number"])

            if page not in seen_pages:

                sources.append(
                    {
                        "page_number": page,
                        "chunk_id": result["chunk_id"],
                    }
                )

                seen_pages.add(page)

        # =========================================================
        # FINAL RESULT
        # =========================================================

        return {
            "answer": answer,

            "sources": sources,

            "usage": {
                "headroom": {
                    "tokens_before": headroom_metrics.get(
                        "tokens_before",
                        0,
                    ),
                    "tokens_after": headroom_metrics.get(
                        "tokens_after",
                        0,
                    ),
                    "tokens_saved": headroom_metrics.get(
                        "tokens_saved",
                        0,
                    ),
                    "compression_ratio": headroom_metrics.get(
                        "compression_ratio",
                        1.0,
                    ),
                    "transforms_applied": headroom_metrics.get(
                        "transforms_applied",
                        [],
                    ),
                },

                "groq": {
                    "input_tokens": groq_metrics.get(
                        "input_tokens",
                        0,
                    ),
                    "output_tokens": groq_metrics.get(
                        "output_tokens",
                        0,
                    ),
                    "total_tokens": groq_metrics.get(
                        "total_tokens",
                        0,
                    ),
                },
            },
        }

    def close(self):
        self.retriever.close()