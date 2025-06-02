from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Embeddings(ABC):
    """Base class for embeddings models."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents."""
        pass
        
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed query."""
        pass 