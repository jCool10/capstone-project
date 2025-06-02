from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Sequence, Iterable

# Import Document từ module cha
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from document import Document

class VectorStore(ABC):
    """Base class for vector stores."""
    
    @abstractmethod
    def add_documents(self, documents: List[Document], **kwargs) -> None:
        """Add documents to the vector store."""
        pass
    
    @abstractmethod
    def add_embeddings(
        self, 
        text_embeddings: Iterable[Tuple[str, List[float]]],
        metadatas: Optional[List[Dict[str, Any]]] = None, 
        **kwargs
    ) -> List[str]:
        """Add embeddings to the vector store."""
        pass
    
    @abstractmethod
    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        **kwargs
    ) -> List[Document]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    def similarity_search_by_vector(
        self, 
        embedding: List[float], 
        k: int = 4, 
        **kwargs
    ) -> List[Document]:
        """Search for similar documents by embedding vector."""
        pass
    
    def as_retriever(self, **kwargs):
        """Create a retriever from the vector store."""
        from ..retrievers import VectorStoreRetriever
        return VectorStoreRetriever(vector_store=self, **kwargs) 