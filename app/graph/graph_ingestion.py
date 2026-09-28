from __future__ import annotations

import json
from pathlib import Path

from app.graph.neo4j_client import Neo4jClient


def ingest_chunks(chunks_path: str) -> None:
    path = Path(chunks_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Support either:
    # {"chunks": [...]}
    # or directly [...]
    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    else:
        chunks = data

    if not chunks:
        raise ValueError("No chunks found in chunks.json")

    document_id = chunks[0]["document_id"]

    client = Neo4jClient()

    try:
        with client.driver.session(
            database=client.database
        ) as session:

            session.run(
                """
                MERGE (d:Document {
                    document_id: $document_id
                })
                SET d.source_type = 'PDF'
                """,
                document_id=document_id,
            )

            session.run(
                """
                UNWIND $chunks AS chunk
                MATCH (d:Document {document_id: $document_id})
                WITH d, chunk
                MERGE (p:Page {
                    document_id: $document_id,
                    page_number: toInteger(chunk.page_number)
                })
                MERGE (d)-[:HAS_PAGE]->(p)
                WITH p, chunk, $document_id AS document_id
                MERGE (c:Chunk {chunk_id: chunk.chunk_id})
                SET
                    c.document_id = document_id,
                    c.page_number = toInteger(chunk.page_number),
                    c.text = chunk.text
                MERGE (p)-[:HAS_CHUNK]->(c)
                """,
                document_id=document_id,
                chunks=[
                    {
                        "chunk_id": chunk["chunk_id"],
                        "page_number": int(chunk["page_number"]),
                        "text": chunk.get("text", ""),
                    }
                    for chunk in chunks
                ],
            )

    finally:
        client.close()

    print("=" * 60)
    print("OKF GRAPH INGESTION")
    print("=" * 60)
    print(f"Document ID : {document_id}")
    print(f"Chunks      : {len(chunks)}")
    print("Status      : SUCCESS")
    print("=" * 60)


if __name__ == "__main__":

    ingest_chunks(
        "data/processed/"
        "d24e34c5ea8d44898d4b967a953c4c61/"
        "chunks.json"
    )