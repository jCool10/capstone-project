from abc import ABC
from typing import Optional, List, Dict, Union



class BaseReranker(ABC):
    @classmethod    
    def class_name(cls) -> str:
        return 'BaseNodeReranker'
    
    def get_ranker(
        self,
        query_node: Union[str, List[str]] = None,
        text_bundle: Union[str, List[str]] = None
    ) -> List[float]:
        """Reranker nodes"""
        
        if query_node is None or text_bundle is None:
            raise ValueError("Query node or Text Bundle is not None")
        
        if isinstance(query_node, list) and isinstance(text_bundle, list):
            assert len(text_bundle) / len(query_node) 
        
        if isinstance(query_node, str) and isinstance(text_bundle, list):
            query_node = [query_node] * len(text_bundle)
            
        return self._get_ranker(query_node, text_bundle)
    
    def _get_ranker(
        self,
        query_node: Union[List[str], str] = None,
        text_bundle: Union[List[str], str] = None
    ) -> Dict[str, str]:
        """ Implement rerank inference"""
    