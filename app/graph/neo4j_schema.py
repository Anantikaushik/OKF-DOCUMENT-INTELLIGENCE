from __future__ import annotations

from app.graph.neo4j_client import Neo4jClient


SCHEMA_QUERIES = [
    """
    CREATE CONSTRAINT document_id_unique IF NOT EXISTS
    FOR (d:Document)
    REQUIRE d.document_id IS UNIQUE
    """,

    """
    CREATE CONSTRAINT page_unique IF NOT EXISTS
    FOR (p:Page)
    REQUIRE (p.document_id, p.page_number) IS UNIQUE
    """,

    """
    CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
    FOR (c:Chunk)
    REQUIRE c.chunk_id IS UNIQUE
    """,

    """
    CREATE INDEX entity_name_index IF NOT EXISTS
    FOR (e:Entity)
    ON (e.name)
    """,
]


def create_schema() -> None:

    client = Neo4jClient()

    try:

        with client.driver.session(
            database=client.database
        ) as session:

            for query in SCHEMA_QUERIES:
                session.run(query)

        print("✅ Neo4j schema created successfully.")

    finally:
        client.close()


if __name__ == "__main__":
    create_schema()