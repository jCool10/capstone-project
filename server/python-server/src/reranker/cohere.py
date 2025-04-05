import os
from typing import Any, List, Optional

from src.bridge.pydantic import Field, PrivateAttr
from src.node.base_node import NodeWithScore

from .base_reranker import BaseReranker


class CohereRerank(BaseReranker):
    model: str = Field(description="Cohere model name.")
    top_n: int = Field(description="Top N nodes to return.")

    _client: Any = PrivateAttr()

    def __init__(
        self,
        top_n: int = 2,
        model: str = "rerank-english-v2.0",
        api_key: Optional[str] = None,
    ):
        try:
            api_key = api_key or os.environ["COHERE_API_KEY"]
        except IndexError:
            raise ValueError(
                "Must pass in cohere api key or "
                "specify via COHERE_API_KEY environment variable "
            )
        try:
            from cohere import Client
        except ImportError:
            raise ImportError(
                "Cannot import cohere package, please `pip install cohere`."
            )

        self._client = Client(api_key=api_key)
        self.top_n = top_n
        self.model = model

    @classmethod
    def class_name(cls) -> str:
        return "CohereRerank"

    def _get_ranker(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[str] = None,
    ) -> List[NodeWithScore]:
        if query_bundle is None:
            raise ValueError("Missing query bundle in extra info.")
        if len(nodes) == 0:
            return []
        
        texts = [node.node.get_content() for node in nodes]
        results = self._client.rerank(
            model=self.model,
            top_n=self.top_n,
            query=query_bundle,
            documents=texts,
        )

        new_nodes = []
        for result in results:
            new_node_with_score = NodeWithScore(
                node=nodes[result.index].node, score=result.relevance_score
            )
            new_nodes.append(new_node_with_score)

        return new_nodes