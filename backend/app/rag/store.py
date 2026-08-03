import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from .models import ProcessedChunk
from dotenv import load_dotenv

load_dotenv()

QDRANT_PATH = "./qdrant_data"
COLLECTION_NAME = "aitinerary_knowledge"

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(path=QDRANT_PATH)

def get_embeddings():
    # Uses BAAI/bge-small-en-v1.5 from Hugging Face via FastEmbed locally
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def init_db():
    client = get_qdrant_client()
    # Recreate collection to ensure proper dimension (384)
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Created collection '{COLLECTION_NAME}' (384-dim FastEmbed) in Qdrant.")

def upsert_documents(chunks: List[ProcessedChunk]):
    client = get_qdrant_client()
    embeddings = get_embeddings()
    
    # Convert ProcessedChunk to LangChain Documents
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk.content,
            metadata=chunk.metadata.model_dump()
        )
        documents.append(doc)
        
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    
    vector_store.add_documents(documents)
    print(f"Upserted {len(documents)} documents to Qdrant.")

from qdrant_client.models import Filter, FieldCondition, MatchValue

def search_documents(query: str, destination_tag: str, limit: int = 5) -> List[Document]:
    client = get_qdrant_client()
    embeddings = get_embeddings()
    
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    
    # Filter by metadata.destination_tag
    qdrant_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.destination_tag",
                match=MatchValue(value=destination_tag)
            )
        ]
    )
    
    # Perform similarity search with filter
    results = vector_store.similarity_search(
        query=query,
        k=limit,
        filter=qdrant_filter
    )
    return results
