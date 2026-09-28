from __future__ import annotations

from pathlib import Path

from app.graph.neo4j_client import Neo4jClient
from app.retrieval.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GraphRetriever:

    def __init__(self):
        self.client = Neo4jClient()
        self.vector_store = VectorStore()

    def _resolve_index_path(self, document_id: str) -> Path:
        if not document_id:
            return PROJECT_ROOT / "data" / "processed" / "missing" / "vector_index.json"

        relative_path = (
            PROJECT_ROOT / "data" / "processed" / document_id / "vector_index.json"
        )

        if relative_path.exists():
            return relative_path

        legacy_path = Path("data") / "processed" / document_id / "vector_index.json"
        if legacy_path.exists():
            return legacy_path

        return relative_path

    def retrieve(
        self,
        query: str,
        document_id: str,
        top_k: int = 5,
    ) -> list[dict]:

        index_path = self._resolve_index_path(document_id)

        if not index_path.exists():
            try:
                from app.ingestion.document_manager import DocumentManager

                DocumentManager().process_document(document_id)
            except Exception:
                return []

            index_path = self._resolve_index_path(document_id)

            if not index_path.exists():
                return []

        # 1. Semantic retrieval
        candidates = self.vector_store.search(
            query=query,
            index_path=str(index_path),
            top_k=top_k,
        )

        if not candidates:
            return []

        chunk_ids = [
            item["chunk_id"]
            for item in candidates
        ]

        # 2. Get authoritative provenance from Neo4j
        provenance = {}

        try:
            cypher = """
            MATCH (d:Document {document_id: $document_id})
                  -[:HAS_PAGE]->(p:Page)
                  -[:HAS_CHUNK]->(c:Chunk)

            WHERE c.chunk_id IN $chunk_ids

            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)

            RETURN
                c.chunk_id AS chunk_id,
                c.text AS text,
                p.page_number AS page_number,
                collect(DISTINCT e.name) AS entities
            """

            with self.client.driver.session(
                database=self.client.database
            ) as session:

                records = session.run(
                    cypher,
                    document_id=document_id,
                    chunk_ids=chunk_ids,
                )

                provenance = {
                    record["chunk_id"]: {
                        "chunk_id": record["chunk_id"],
                        "text": record["text"],
                        "page_number": record["page_number"],
                        "entities": record["entities"],
                    }
                    for record in records
                }
        except Exception:
            provenance = {}

        # 3. Combine semantic score + Neo4j provenance (fallback to vector chunks)
        results = []

        for candidate in candidates:

            chunk_id = candidate["chunk_id"]
            source = provenance.get(chunk_id)

            if source:
                results.append(
                    {
                        **source,
                        "similarity": candidate["similarity"],
                    }
                )
                continue

            results.append(
                {
                    "chunk_id": chunk_id,
                    "text": candidate.get("text", ""),
                    "page_number": int(candidate.get("page_number", 0)),
                    "entities": [],
                    "similarity": candidate["similarity"],
                }
            )

        return results

    def close(self):
        self.client.close()