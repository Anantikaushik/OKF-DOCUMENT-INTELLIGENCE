from app.graph.neo4j_client import Neo4jClient


def main():

    print("=" * 60)
    print("NEO4J CONNECTION TEST")
    print("=" * 60)

    client = Neo4jClient()

    try:

        connected = client.verify_connection()

        if connected:
            print("✅ Neo4j connection successful.")
        else:
            print("❌ Neo4j connection failed.")

    finally:

        client.close()


if __name__ == "__main__":
    main()