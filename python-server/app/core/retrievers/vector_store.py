from typing import List, Dict, Any, Optional

from .base import BaseRetriever
from ..document import Document
from ..vector_stores.base import VectorStore

class VectorStoreRetriever(BaseRetriever):
    """Retriever that uses a vector store."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with a vector store."""
        self.vector_store = vector_store
        self.search_type = search_type
        self.search_kwargs = search_kwargs or {}
        
    def get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Get documents relevant to a query."""
        search_kwargs = {**self.search_kwargs, **kwargs}
        
        if self.search_type == "similarity":
            docs = self.vector_store.similarity_search(query, **search_kwargs)
        elif self.search_type == "mmr":
            if hasattr(self.vector_store, "max_marginal_relevance_search"):
                docs = self.vector_store.max_marginal_relevance_search(query, **search_kwargs)
            else:
                raise ValueError(
                    f"Vector store {self.vector_store.__class__.__name__} does not support MMR search"
                )
        else:
            raise ValueError(f"Search type {self.search_type} not supported")
            
        return docs 