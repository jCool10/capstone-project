from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import CrossEncoder

class Reranker:
    """Rerank retrieved documents based on relevance to query."""
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "auto",
        top_k: int = 3
    ):
        """Initialize reranker with model and parameters."""
        self.model_name = model_name
        self.top_k = top_k
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device
            
        # Load model
        self.model = CrossEncoder(model_name, device=self.device)
        
    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank documents based on relevance to query."""
        if not documents:
            return []
            
        # Prepare document pairs for scoring
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Get relevance scores
        scores = self.model.predict(pairs)
        
        # Sort documents by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k documents
        return [doc for doc, _ in scored_docs[:self.top_k]] 