from typing import List, Dict, Tuple, Any
from collections import defaultdict
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ScoreFusion:
    """Score fusion algorithms for hybrid search."""
    
    @staticmethod
    def normalize_scores(results: List[Dict], score_key: str) -> List[Dict]:
        """
        Normalize scores to 0-1 range using min-max normalization
        
        Args:
            results: List of result dictionaries
            score_key: Key name for the score to normalize
            
        Returns:
            Results with normalized scores
        """
        if not results:
            return results
            
        scores = [r.get(score_key, 0) for r in results]
        if not scores:
            return results
            
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score != min_score else 1
        
        normalized_results = []
        for result in results:
            result_copy = result.copy()
            original_score = result.get(score_key, 0)
            normalized_score = (original_score - min_score) / score_range
            result_copy[f"normalized_{score_key}"] = normalized_score
            normalized_results.append(result_copy)
            
        return normalized_results
        
    @staticmethod
    def reciprocal_rank_fusion(dense_results: List[Dict], 
                             sparse_results: List[Dict], 
                             k: int = 60) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm
        
        Formula: RRF Score = Σ(1 / (k + rank_i))
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval  
            k: Rank constant (default: 60)
            
        Returns:
            List of (doc_id, score) tuples sorted by score
        """
        scores = defaultdict(float)
        
        # Process dense results
        for rank, result in enumerate(dense_results):
            doc_id = result.get("id", "")
            if doc_id:
                scores[doc_id] += 1 / (k + rank + 1)
                
        # Process sparse results
        for rank, result in enumerate(sparse_results):
            doc_id = result.get("id", "")
            if doc_id:
                scores[doc_id] += 1 / (k + rank + 1)
                
        # Sort by score descending
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"RRF fusion: Combined {len(dense_results)} dense + {len(sparse_results)} sparse results into {len(sorted_scores)} unique documents")
        
        return sorted_scores
        
    @staticmethod
    def linear_combination_fusion(dense_results: List[Dict],
                                sparse_results: List[Dict],
                                alpha: float = 0.5) -> List[Tuple[str, float]]:
        """
        Linear combination of normalized scores
        
        Formula: Combined Score = α × Dense Score + (1-α) × Sparse Score
        
        Args:
            dense_results: Results from dense retrieval (normalized)
            sparse_results: Results from sparse retrieval (normalized)
            alpha: Weight for dense scores (0-1)
            
        Returns:
            List of (doc_id, score) tuples sorted by score
        """
        scores = defaultdict(float)
        
        # Process dense results
        for result in dense_results:
            doc_id = result.get("id", "")
            if doc_id:
                # Use normalized score or fall back to original
                dense_score = result.get("normalized_vector_score", 
                                       result.get("normalized_distance", 
                                                result.get("vector_score", 0)))
                scores[doc_id] += alpha * dense_score
                
        # Process sparse results  
        for result in sparse_results:
            doc_id = result.get("id", "")
            if doc_id:
                sparse_score = result.get("normalized_bm25_score",
                                        result.get("bm25_score", 0))
                scores[doc_id] += (1 - alpha) * sparse_score
                
        # Sort by score descending
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"Linear fusion (α={alpha}): Combined {len(dense_results)} dense + {len(sparse_results)} sparse results into {len(sorted_scores)} unique documents")
        
        return sorted_scores
        
    @staticmethod
    def combine_results(dense_results: List[Dict],
                       sparse_results: List[Dict],
                       fusion_scores: List[Tuple[str, float]],
                       fusion_method: str) -> List[Dict]:
        """
        Combine results from different retrievers with fusion scores
        
        Args:
            dense_results: Dense retrieval results
            sparse_results: Sparse retrieval results
            fusion_scores: List of (doc_id, fused_score) tuples
            fusion_method: Method used for fusion
            
        Returns:
            Combined results with fusion scores
        """
        # Create lookup maps
        dense_map = {r.get("id"): r for r in dense_results}
        sparse_map = {r.get("id"): r for r in sparse_results}
        
        combined_results = []
        
        for doc_id, fusion_score in fusion_scores:
            # Get the result from either dense or sparse (prefer dense)
            if doc_id in dense_map:
                result = dense_map[doc_id].copy()
                result["retrieval_method"] = "dense" if doc_id not in sparse_map else "both"
            elif doc_id in sparse_map:
                result = sparse_map[doc_id].copy()
                result["retrieval_method"] = "sparse"
            else:
                continue
                
            # Add fusion information
            result["fusion_score"] = fusion_score
            result["fusion_method"] = fusion_method
            
            # Add individual scores for transparency
            if doc_id in dense_map:
                result["dense_score"] = dense_map[doc_id].get("vector_score", 0)
            if doc_id in sparse_map:
                result["sparse_score"] = sparse_map[doc_id].get("bm25_score", 0)
                
            combined_results.append(result)
            
        return combined_results
        
    @staticmethod
    def get_fusion_stats(dense_results: List[Dict],
                        sparse_results: List[Dict],
                        final_results: List[Dict]) -> Dict[str, Any]:
        """
        Get statistics about the fusion process
        
        Args:
            dense_results: Original dense results
            sparse_results: Original sparse results
            final_results: Final fused results
            
        Returns:
            Dictionary with fusion statistics
        """
        dense_ids = set(r.get("id") for r in dense_results)
        sparse_ids = set(r.get("id") for r in sparse_results)
        final_ids = set(r.get("id") for r in final_results)
        
        overlap = dense_ids.intersection(sparse_ids)
        
        stats = {
            "dense_count": len(dense_results),
            "sparse_count": len(sparse_results),
            "final_count": len(final_results),
            "overlap_count": len(overlap),
            "overlap_ratio": len(overlap) / max(len(dense_ids.union(sparse_ids)), 1),
            "dense_contribution": len(final_ids.intersection(dense_ids)) / max(len(final_ids), 1),
            "sparse_contribution": len(final_ids.intersection(sparse_ids)) / max(len(final_ids), 1)
        }
        
        return stats 