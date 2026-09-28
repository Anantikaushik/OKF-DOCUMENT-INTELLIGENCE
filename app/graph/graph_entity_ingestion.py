from __future__ import annotations

import json
from pathlib import Path

from app.graph.neo4j_client import Neo4jClient
from app.graph.entity_extractor import EntityExtractor


def ingest_entities(chunks_path: str) -> None:

    path = Path(chunks_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", []) if isinstance(data, dict) else data

    if not chunks:
        raise ValueError("No chunks found.")

    extractor = EntityExtractor()
    client = Neo4jClient()

    total_entities = 0
    total_relationships = 0

    try:

        with client.driver.session(
            database=client.database
        ) as session:

            for index, chunk in enumerate(chunks, start=1):

                chunk_id = chunk["chunk_id"]
                document_id = chunk["document_id"]
                page_number = int(chunk["page_number"])
                text = chunk["text"]

                print(
                    f"[{index}/{len(chunks)}] "
                    f"Processing page {page_number}..."
                )

                result = extractor.extract(text)

                entities = result.get("entities", [])
                relationships = result.get(
                    "relationships", []
                )

                # -------------------------------------------------
                # Create entities
                # -------------------------------------------------
                valid_entities = []
                for entity in entities:
                    name = str(entity.get("name", "")).strip()
                    if not name:
                        continue
                    valid_entities.append(
                        {
                            "name": name,
                            "type": str(entity.get("type", "unknown")),
                            "description": str(entity.get("description", "")),
                        }
                    )

                if valid_entities:
                    session.run(
                        """
                        UNWIND $entities AS entity
                        MATCH (c:Chunk {chunk_id: $chunk_id})
                        MERGE (e:Entity {name: entity.name})
                        SET
                            e.type = entity.type,
                            e.description = entity.description
                        MERGE (c)-[:MENTIONS]->(e)
                        """,
                        chunk_id=chunk_id,
                        entities=valid_entities,
                    )
                    total_entities += len(valid_entities)

                # -------------------------------------------------
                # Create relationships
                # -------------------------------------------------
                valid_relationships = []
                for relationship in relationships:
                    source = str(relationship.get("source", "")).strip()
                    target = str(relationship.get("target", "")).strip()
                    relation = str(
                        relationship.get("relationship", "RELATED_TO")
                    ).strip()

                    if not source or not target:
                        continue

                    valid_relationships.append(
                        {
                            "source": source,
                            "target": target,
                            "relationship": relation,
                        }
                    )

                if valid_relationships:
                    session.run(
                        """
                        UNWIND $relationships AS relation
                        MATCH (source:Entity {name: relation.source})
                        MATCH (target:Entity {name: relation.target})
                        MERGE (source)-[r:RELATED_TO]->(target)
                        SET r.relationship = relation.relationship
                        """,
                        relationships=valid_relationships,
                    )
                    total_relationships += len(valid_relationships)

    finally:
        client.close()

    print()
    print("=" * 60)
    print("ENTITY GRAPH INGESTION")
    print("=" * 60)
    print(f"Chunks processed       : {len(chunks)}")
    print(f"Entities processed     : {total_entities}")
    print(f"Relationships processed: {total_relationships}")
    print("Status                 : SUCCESS")
    print("=" * 60)


if __name__ == "__main__":

    ingest_entities(
        "data/processed/"
        "d24e34c5ea8d44898d4b967a953c4c61/"
        "chunks.json"
    )