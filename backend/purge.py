import os
import psycopg
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv(".env")

print("1. Purging Qdrant Vector Database...")
try:
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    # Ignore errors if it doesn't exist
    try:
        qdrant.delete_collection("travel_cards")
    except Exception:
        pass

    qdrant.create_collection(
        collection_name="travel_cards",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )
    # Create payload index for user_id to prevent 400 errors
    qdrant.create_payload_index(
        collection_name="travel_cards",
        field_name="user_id",
        field_schema="integer",
    )
    print(" -> Successfully purged and recreated Qdrant 'travel_cards' collection!")
except Exception as e:
    print(f" -> Qdrant purge failed: {e}")

print("\n2. Purging Postgres Chat Checkpoints...")
postgres_url = os.getenv("DATABASE_POSTGRES_PRISMA_URL")

if not postgres_url:
    print(" -> Error: DATABASE_POSTGRES_PRISMA_URL not found in .env")
else:
    try:
        # Connect using standard psycopg 3
        conn = psycopg.connect(postgres_url, autocommit=True)

        # Execute truncate
        conn.execute("TRUNCATE TABLE checkpoints, checkpoint_blobs, checkpoint_writes CASCADE;")

        print(" -> Successfully purged all LangGraph chat history!")
        conn.close()
    except Exception as e:
        print(f" -> Postgres purge failed: {e}")

print("\nDone! All databases purged.")
