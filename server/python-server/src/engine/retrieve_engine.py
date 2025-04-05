

"""Base query engine."""

import logging
from typing import Any, List, Optional, Tuple

from src.callbacks.callback_manager import CallbackManager
from src.node.base_node import NodeWithScore
from src.retriever.types import QueryBundle, QueryType
from src.retriever.base_retriver import BaseRetriever
from src.reranker.base_reranker import BaseReranker

from .base import BaseEngine

logger = logging.getLogger(__name__)

class RetriverEngine(BaseEngine):
    """Base query engine."""

    def __init__(
        self, 
        callback_manager: Optional[CallbackManager],
        retriever: BaseRetriever,
        reranker: Optional[BaseReranker] = None,
        use_async: bool = False,
        **kwargs: Any,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.use_async = use_async
        self.kwargs = kwargs
        super().__init__(
            callback_manager=callback_manager
        )

    def run_engine(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        return self.search(query_bundle=query_bundle)
    
    async def arun_engine(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        return await self.asearch(query_bundle=query_bundle)

    def search(self, query_bundle: QueryBundle) -> Tuple[List[NodeWithScore], List[NodeWithScore]]:
        nodes = self.retriever.retrieve(query_bundle)
        rerank_nodes = self._rerank_nodes(
            nodes=nodes,
            query_bundle=query_bundle
        )
        return nodes, rerank_nodes

    async def asearch(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = await self.retriever.aretrieve(query_bundle)
        nodes = self._rerank_nodes(
            nodes=nodes,
            query_bundle=query_bundle
        )
        return nodes

    def _rerank_nodes(
        self, 
        nodes: List[NodeWithScore],
        query_bundle: QueryBundle
    ) -> List[NodeWithScore]:
        if self.reranker:
            nodes = self.reranker.get_ranker(
                query_node=query_bundle.query_str, 
                text_bundle=[node.node.get_content() for node in nodes],
            )
        return nodes