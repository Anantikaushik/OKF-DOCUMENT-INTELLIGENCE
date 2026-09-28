from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.model = _get_model(model_name)

    def build_index(self, chunks_path: str, output_path: str) -> None:

        chunks_file = Path(chunks_path)

        if not chunks_file.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {chunks_file}"
            )

        with chunks_file.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        chunks = (
            data.get("chunks", [])
            if isinstance(data, dict)
            else data
        )

        if not chunks:
            raise ValueError("No chunks found.")

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        print(f"Creating embeddings for {len(texts)} chunks...")

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )
        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        output = {
            "model": self.model.get_sentence_embedding_dimension(),
            "model_name": "all-MiniLM-L6-v2",
            "chunks": chunks,
            "embeddings": embeddings.tolist(),
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                output,
                f,
                ensure_ascii=False,
            )

        print(
            f"Vector index created: {output_file}"
        )
        print(
            f"Embedding dimension: {embeddings.shape[1]}"
        )

    def search(
        self,
        query: str,
        index_path: str,
        top_k: int = 5,
    ) -> list[dict]:

        index_file = Path(index_path)

        if not index_file.exists():
            raise FileNotFoundError(
                f"Vector index not found: {index_file}"
            )

        with index_file.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        chunks = data["chunks"]

        embeddings = np.asarray(
            data["embeddings"],
            dtype=np.float32,
        )

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        scores = embeddings @ query_embedding

        top_indices = np.argsort(
            scores
        )[::-1][:top_k]

        results = []

        for index in top_indices:

            chunk = dict(chunks[int(index)])

            chunk["similarity"] = float(
                scores[int(index)]
            )

            results.append(chunk)

        return results


@lru_cache(maxsize=2)
def _get_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)