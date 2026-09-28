import os

import pytest

from app.graph.neo4j_client import Neo4jClient


@pytest.mark.integration
def test_neo4j_connection():

    if not os.getenv("NEO4J_PASSWORD"):
        pytest.skip(
            "NEO4J_PASSWORD is not configured."
        )

    client = Neo4jClient()

    try:
        assert client.verify_connection() is True

    finally:
        client.close()