from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# Initialize Local Qdrant Client (File-based)
qdrant_client = QdrantClient(path="qdrant_db")

# Initialize Gemini Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

COLLECTION_NAME = "travel_cards"

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

def get_qdrant_client():
    return qdrant_client

def get_embeddings():
    return embeddings
