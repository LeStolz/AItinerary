from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class DocumentMetadata(BaseModel):
    doc_type: str = Field(..., description="Type of document, e.g., 'personal_profile' or 'destination_guide'")
    destination_tag: str = Field(..., description="Destination identifier, e.g., 'paris', 'general'")
    headers: Dict[str, Any] = Field(default_factory=dict, description="Header hierarchy from Markdown")
    
class ProcessedChunk(BaseModel):
    content: str = Field(..., description="The actual text content of the chunk")
    metadata: DocumentMetadata = Field(..., description="Metadata associated with the chunk")
