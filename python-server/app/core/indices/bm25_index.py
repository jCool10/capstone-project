from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import pickle
import os
import logging
import numpy as np

from ..document import Document

logger = logging.getLogger(__name__)

class VietnameseBM25Index:
    """BM25 Index với hỗ trợ tiếng Việt và persistence."""
    
    def __init__(self, collection_name: str, k1: float = 1.2, b: float = 0.75):
        """
        Initialize Vietnamese BM25 Index
        
        Args:
            collection_name: Name of the collection
            k1: BM25 k1 parameter (term frequency saturation point)
            b: BM25 b parameter (field length normalization)
        """
        self.collection_name = collection_name
        
        # Ensure parameters are numeric
        self.k1 = float(k1)
        self.b = float(b)
        
        # Index state
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.tokenized_corpus = []
        
        logger.info(f"VietnameseBM25Index initialized for '{collection_name}' with k1={self.k1}, b={self.b}")
        
    def preprocess_text(self, text: str) -> List[str]:
        """
        Vietnamese text preprocessing
        
        Args:
            text: Input text to preprocess
            
        Returns:
            List of tokens
        """
        try:
            # Try to use underthesea for Vietnamese tokenization
            try:
                from underthesea import word_tokenize
                tokens = word_tokenize(text.lower())
            except ImportError:
                logger.warning("underthesea not available, using simple tokenization")
                # Fallback to simple tokenization
                tokens = text.lower().split()
            
            # Remove stopwords, punctuation and keep only alphanumeric
            tokens = [token for token in tokens if token.isalnum() and len(token) > 1]
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error in text preprocessing: {e}")
            # Fallback to simple split
            return text.lower().split()
            
    def build_index(self, documents: List[Document]):
        """
        Build BM25 index from documents
        
        Args:
            documents: List of Document objects
        """
        logger.info(f"Building BM25 index with {len(documents)} documents")
        
        corpus = []
        self.documents = documents
        
        # Ensure all doc IDs are strings
        self.doc_ids = []
        for doc in documents:
            doc_id = doc.id_
            if not isinstance(doc_id, str):
                doc_id = str(doc_id)
            self.doc_ids.append(doc_id)
        
        for doc in documents:
            tokens = self.preprocess_text(doc.page_content)
            corpus.append(tokens)
            
        self.tokenized_corpus = corpus
        
        # Build BM25 index
        self.bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)
        
        logger.info(f"BM25 index built successfully with {len(corpus)} documents")
        
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search using BM25
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of search results with scores
        """
        if not self.bm25:
            logger.warning("BM25 index not built yet")
            return []
            
        try:
            query_tokens = self.preprocess_text(query)
            if not query_tokens:
                logger.warning("Empty query after preprocessing")
                return []
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top k results
            top_indices = np.argsort(scores)[-top_k:][::-1]
            
            results = []
            for i, idx in enumerate(top_indices):
                if idx < len(self.documents) and scores[idx] > 0:  # Only positive scores
                    doc = self.documents[idx]
                    doc_id = self.doc_ids[idx] if idx < len(self.doc_ids) else str(doc.id_)
                    
                    # Ensure metadata is properly serializable
                    metadata = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
                    
                    # Convert any non-serializable values to strings
                    for key, value in metadata.items():
                        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            metadata[key] = str(value)
                    
                    result_dict = {
                        "id": doc_id,
                        "text": doc.page_content,
                        "metadata": metadata,
                        "bm25_score": float(scores[idx]),
                        "method": "bm25"
                    }
                    
                    results.append(result_dict)
                    
            logger.info(f"BM25 search returned {len(results)} results for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
        
    def add_documents(self, new_documents: List[Document]):
        """
        Add new documents to existing index
        
        Args:
            new_documents: List of new Document objects
        """
        if not self.bm25:
            logger.info("No existing index, building new index")
            self.build_index(new_documents)
            return
            
        logger.info(f"Adding {len(new_documents)} new documents to existing index")
        
        # Add to existing documents
        self.documents.extend(new_documents)
        
        # Add new doc IDs (ensure they're strings)
        for doc in new_documents:
            doc_id = doc.id_
            if not isinstance(doc_id, str):
                doc_id = str(doc_id)
            self.doc_ids.append(doc_id)
        
        # Tokenize new documents
        new_corpus = []
        for doc in new_documents:
            tokens = self.preprocess_text(doc.page_content)
            new_corpus.append(tokens)
            
        self.tokenized_corpus.extend(new_corpus)
        
        # Rebuild index with all documents
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)
        
        logger.info(f"Index updated with {len(self.documents)} total documents")
        
    def save_index(self, filepath: str):
        """
        Save BM25 index to disk
        
        Args:
            filepath: Path to save the index
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                "bm25": self.bm25,
                "documents": self.documents,
                "doc_ids": self.doc_ids,
                "tokenized_corpus": self.tokenized_corpus,
                "k1": self.k1,
                "b": self.b
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
                
            logger.info(f"BM25 index saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving BM25 index: {e}")
            
    def load_index(self, filepath: str) -> bool:
        """
        Load BM25 index from disk
        
        Args:
            filepath: Path to load the index from
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Index file not found: {filepath}")
                return False
                
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                
            self.bm25 = data["bm25"]
            self.documents = data["documents"]
            self.doc_ids = data["doc_ids"]
            self.tokenized_corpus = data.get("tokenized_corpus", [])
            self.k1 = data["k1"]
            self.b = data["b"]
            
            logger.info(f"BM25 index loaded from {filepath} with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error loading BM25 index: {e}")
            return False
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Dictionary containing index statistics
        """
        if not self.bm25:
            return {"status": "not_built"}
            
        return {
            "status": "ready",
            "num_documents": len(self.documents),
            "num_tokens": sum(len(tokens) for tokens in self.tokenized_corpus),
            "avg_doc_length": np.mean([len(tokens) for tokens in self.tokenized_corpus]) if self.tokenized_corpus else 0,
            "k1": self.k1,
            "b": self.b
        }
        
    def clear_index(self):
        """Clear the current index"""
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.tokenized_corpus = []
        logger.info("BM25 index cleared") 