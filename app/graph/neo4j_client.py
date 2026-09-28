from __future__ import annotations

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class Neo4jClient:

    def __init__(self) -> None:

        self.uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )

        self.username = os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = os.getenv(
            "NEO4J_PASSWORD",
        )

        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j",
        )

        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD is not configured."
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def verify_connection(self) -> bool:

        with self.driver.session(
            database=self.database
        ) as session:

            result = session.run(
                "RETURN 1 AS result"
            )

            record = result.single()

            return (
                record is not None
                and record["result"] == 1
            )

    def close(self) -> None:

        self.driver.close()