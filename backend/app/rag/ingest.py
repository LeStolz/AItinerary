import os
import json
from pathlib import Path
from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter
from .models import ProcessedChunk, DocumentMetadata
from .store import init_db, upsert_documents

def ingest_directory(data_dir: str):
    init_db()
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    chunks: List[ProcessedChunk] = []
    
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Data directory {data_dir} does not exist. Creating it.")
        data_path.mkdir(parents=True, exist_ok=True)
        # Create subdirectories for profiles and destinations
        (data_path / "profiles").mkdir(exist_ok=True)
        (data_path / "destinations").mkdir(exist_ok=True)
        return
        
    for root, _, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            
            # Determine doc_type and destination_tag based on folder structure or filename
            doc_type = "general"
            if "profiles" in str(file_path):
                doc_type = "personal_profile"
            elif "destinations" in str(file_path):
                doc_type = "destination_guide"
                
            # For simplicity, extract destination tag from filename if it's a destination guide
            destination_tag = "general"
            if doc_type == "destination_guide":
                destination_tag = file_path.stem.lower() # e.g. "paris.md" -> "paris"
                
            if file_path.suffix == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                splits = markdown_splitter.split_text(content)
                for split in splits:
                    metadata = DocumentMetadata(
                        doc_type=doc_type,
                        destination_tag=destination_tag,
                        headers=split.metadata
                    )
                    chunk = ProcessedChunk(
                        content=split.page_content,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = json.dumps(data)
                    metadata = DocumentMetadata(
                        doc_type=doc_type,
                        destination_tag=destination_tag,
                        headers={}
                    )
                    chunk = ProcessedChunk(
                        content=content,
                        metadata=metadata
                    )
                    chunks.append(chunk)

    if chunks:
        upsert_documents(chunks)
        print(f"Successfully ingested {len(chunks)} chunks.")
    else:
        print("No documents found to ingest.")

if __name__ == "__main__":
    # Test execution
    ingest_directory(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data")))
