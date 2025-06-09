from typing import Dict, List, Any, Optional
import logging
import time
import os

from ..indices import VietnameseBM25Index
from ..fusion import ScoreFusion
from ..vector_stores.milvus import MilvusVectorStore

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """
    Hybrid Search Engine combining dense (vector) and sparse (BM25) retrieval
    """
    
    def __init__(self, 
                 vector_store: MilvusVectorStore,
                 config: Dict[str, Any]):
        """
        Initialize Hybrid Search Engine
        
        Args:
            vector_store: Milvus vector store for dense retrieval
            config: Configuration dictionary
        """
        self.vector_store = vector_store
        self.config = config
        
        # Initialize BM25 indices for different collections
        self.bm25_indices = {}
        
        # Score fusion utility
        self.score_fusion = ScoreFusion()
        
        logger.info("Hybrid Search Engine initialized")
        
    def get_or_create_bm25_index(self, collection_name: str) -> Optional[VietnameseBM25Index]:
        """
        Get or create BM25 index for a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            BM25 index instance or None if failed
        """
        if collection_name not in self.bm25_indices:
            # Create new BM25 index
            bm25_config = self.config.get("hybrid_search", {}).get("bm25", {})
            bm25_index = VietnameseBM25Index(
                collection_name=collection_name,
                k1=bm25_config.get("k1", 1.2),
                b=bm25_config.get("b", 0.75)
            )
            
            # Try to load existing index
            index_path = self._get_bm25_index_path(collection_name)
            if bm25_index.load_index(index_path):
                logger.info(f"Loaded existing BM25 index for collection: {collection_name}")
            else:
                logger.info(f"No existing BM25 index found for collection: {collection_name}")
                
            self.bm25_indices[collection_name] = bm25_index
            
        return self.bm25_indices.get(collection_name)
        
    def _get_bm25_index_path(self, collection_name: str) -> str:
        """Get the file path for BM25 index"""
        index_dir = self.config.get("bm25_index_dir", "data/bm25_indices")
        return os.path.join(index_dir, f"{collection_name}.pkl")
        
    def build_bm25_index(self, collection_name: str, documents: List[Any]) -> bool:
        """
        Build BM25 index for a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of Document objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            bm25_index = self.get_or_create_bm25_index(collection_name)
            if not bm25_index:
                return False
                
            # Build the index
            bm25_index.build_index(documents)
            
            # Save to disk
            index_path = self._get_bm25_index_path(collection_name)
            bm25_index.save_index(index_path)
            
            logger.info(f"BM25 index built and saved for collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error building BM25 index for {collection_name}: {e}")
            return False
            
    def search(self,
               query: str,
               collection_name: str,
               top_k: int = 5,
               use_hybrid: bool = True,
               **kwargs) -> Dict[str, Any]:
        """
        Perform hybrid search combining dense and sparse retrieval
        
        Args:
            query: Search query
            collection_name: Collection to search in
            top_k: Number of final results to return
            use_hybrid: Whether to use hybrid search
            **kwargs: Additional search parameters
            
        Returns:
            Search results dictionary
        """
        start_time = time.time()
        
        try:
            # Get configuration
            hybrid_config = self.config.get("hybrid_search", {})
            initial_k = hybrid_config.get("initial_k", 20)
            fusion_method = hybrid_config.get("fusion_method", "rrf")
            dense_weight = hybrid_config.get("dense_weight", 0.6)
            
            if not use_hybrid or not hybrid_config.get("enabled", False):
                # Fall back to dense search only
                return self._dense_search_only(query, collection_name, top_k)
                
            # Get BM25 index
            bm25_index = self.get_or_create_bm25_index(collection_name)
            if not bm25_index or not bm25_index.bm25:
                logger.warning(f"BM25 index not available for {collection_name}, falling back to dense search")
                return self._dense_search_only(query, collection_name, top_k)
                
            # Parallel retrieval
            dense_results = self._get_dense_results(query, collection_name, initial_k)
            sparse_results = self._get_sparse_results(query, collection_name, initial_k)
            
            # Score fusion
            if fusion_method == "rrf":
                fusion_scores = self.score_fusion.reciprocal_rank_fusion(
                    dense_results, sparse_results
                )
            else:  # linear fusion
                # Normalize scores first
                dense_results = self.score_fusion.normalize_scores(dense_results, "vector_score")
                sparse_results = self.score_fusion.normalize_scores(sparse_results, "bm25_score")
                
                fusion_scores = self.score_fusion.linear_combination_fusion(
                    dense_results, sparse_results, alpha=dense_weight
                )
                
            # Combine results
            final_results = self.score_fusion.combine_results(
                dense_results, sparse_results, fusion_scores[:top_k], fusion_method
            )
            
            # Get fusion statistics
            fusion_stats = self.score_fusion.get_fusion_stats(
                dense_results, sparse_results, final_results
            )
            
            search_time = time.time() - start_time
            
            return {
                "success": True,
                "results": final_results,
                "search_method": "hybrid",
                "fusion_method": fusion_method,
                "total_results": len(final_results),
                "search_time": search_time,
                "fusion_stats": fusion_stats
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fall back to dense search
            return self._dense_search_only(query, collection_name, top_k)
            
    def _get_dense_results(self, query: str, collection_name: str, k: int) -> List[Dict]:
        """Get dense retrieval results from Milvus"""
        try:
            results = self.vector_store.query(
                query=query,
                collection_name=collection_name,
                limit=k,
                hybrid_search=False,
                rerank=False
            )
            
            # Ensure consistent format
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id", ""),
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "vector_score": result.get("distance", result.get("vector_score", 0)),
                    "method": "dense"
                }
                formatted_results.append(formatted_result)
                
            logger.info(f"Dense search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in dense retrieval: {e}")
            return []
            
    def _get_sparse_results(self, query: str, collection_name: str, k: int) -> List[Dict]:
        """Get sparse retrieval results from BM25"""
        try:
            bm25_index = self.bm25_indices.get(collection_name)
            if not bm25_index:
                return []
                
            results = bm25_index.search(query, top_k=k)
            logger.info(f"Sparse search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in sparse retrieval: {e}")
            return []
            
    def _dense_search_only(self, query: str, collection_name: str, top_k: int) -> Dict[str, Any]:
        """Fall back to dense search only"""
        start_time = time.time()
        
        try:
            results = self.vector_store.query(
                query=query,
                collection_name=collection_name,
                limit=top_k
            )
            
            search_time = time.time() - start_time
            
            return {
                "success": True,
                "results": results,
                "search_method": "dense_fallback",
                "total_results": len(results),
                "search_time": search_time
            }
            
        except Exception as e:
            logger.error(f"Error in dense fallback search: {e}")
            return {
                "success": False,
                "results": [],
                "search_method": "failed",
                "error": str(e)
            }
            
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "collection_name": collection_name,
            "dense_index": {"status": "unknown"},
            "sparse_index": {"status": "not_built"}
        }
        
        # Check dense index (Milvus)
        try:
            # This would depend on your Milvus implementation
            stats["dense_index"] = {"status": "available"}
        except Exception as e:
            stats["dense_index"] = {"status": "error", "error": str(e)}
            
        # Check sparse index (BM25)
        bm25_index = self.bm25_indices.get(collection_name)
        if bm25_index:
            stats["sparse_index"] = bm25_index.get_stats()
        else:
            # Try to check if index file exists
            index_path = self._get_bm25_index_path(collection_name)
            if os.path.exists(index_path):
                stats["sparse_index"] = {"status": "available_on_disk"}
                
        return stats
        
    def clear_bm25_index(self, collection_name: str) -> bool:
        """
        Clear BM25 index for a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful
        """
        try:
            if collection_name in self.bm25_indices:
                self.bm25_indices[collection_name].clear_index()
                del self.bm25_indices[collection_name]
                
            # Remove index file
            index_path = self._get_bm25_index_path(collection_name)
            if os.path.exists(index_path):
                os.remove(index_path)
                
            logger.info(f"BM25 index cleared for collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing BM25 index for {collection_name}: {e}")
            return False 