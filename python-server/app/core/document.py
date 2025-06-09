from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import uuid

@dataclass
class Document:
    """Document class for storing text and metadata."""
    
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id_: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def excluded_llm_metadata_keys(self) -> List[str]:
        """Keys to exclude from metadata when passing to LLM."""
        return self.metadata.get("excluded_llm_metadata_keys", [])
    
    @property
    def excluded_embed_metadata_keys(self) -> List[str]:
        """Keys to exclude from metadata when embedding."""
        return self.metadata.get("excluded_embed_metadata_keys", [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id_,
            "page_content": self.page_content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create from dictionary."""
        return cls(
            page_content=data["page_content"],
            metadata=data.get("metadata", {}),
            id_=data.get("id", str(uuid.uuid4()))
        ) 