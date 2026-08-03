from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if qdrant_url and qdrant_api_key:
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
else:
    qdrant_client = QdrantClient(path="qdrant_db")

# Initialize Gemini Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

COLLECTION_NAME = "travel_cards"

from qdrant_client.http.models import PayloadSchemaType

# Ensure collection exists with correct dimensions (Gemini-2 is 3072)
try:
    col = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    if col.config.params.vectors.size != 3072:
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
except Exception:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )

try:
    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="user_id",
        field_schema=PayloadSchemaType.INTEGER,
    )
except Exception:
    pass

def get_qdrant_client():
    return qdrant_client

def get_embeddings():
    return embeddings
