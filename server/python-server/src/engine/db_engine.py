"""Base data ingestion engine."""

import logging
from typing import Any, List, Dict, Optional, Sequence

from src.callbacks.callback_manager import CallbackManager
from src.node.base_node import BaseNode, MetadataMode
from src.node_parser.base import NodeParser
from src.vector_stores.base_vector import VectorStore
from src.core.service_context import ServiceContext
from src.core.storage_context import StorageContext
from src.utils.utils import iter_batch

from .base import BaseEngine

logger = logging.getLogger(__name__)

class DatabaseEngine(BaseEngine):
    """Add nodes with embedding to vector store

    NOTE: Overrides BaseIndex.build_index_from_nodes.
    VectorStoreIndex only stores nodes in document store
    if vector store does not store text
    """


    def __init__(
        self, 
        insert_batch_size: int,
        callback_manager: Optional[CallbackManager],
        name_vector_store: str,
        service_context: ServiceContext,
        storage_context: StorageContext,
        **kwargs: Any,
    ):
        self._insert_batch_size=insert_batch_size
        self._service_context = service_context
        self._storage_context = storage_context
        self._vector_store: VectorStore = self._storage_context.get_vector_store(name_vector_store=name_vector_store)
        self.kwargs = kwargs
        super().__init__(callback_manager=callback_manager)

    def run_engine(self, nodes: Sequence[BaseNode], show_progress: bool = False) -> None:
        return self._add_nodes_to_index(nodes=nodes, show_progress=show_progress)    
    
    def arun_engine(self, nodes: Sequence[BaseNode], show_progress: bool = False):
        return self._async_add_nodes_to_index(nodes=nodes, show_progress=show_progress) 
    
    def is_validate_nodes(
        self,
        nodes: Sequence[BaseNode],
    ) -> Sequence[BaseNode]:
        """Validating node."""
        # raise an error if even one node has no content
        for node in nodes:
            if node.get_content(metadata_mode=MetadataMode.EMBED) == "":
                raise ValueError(
                    "Cannot build index from nodes with no content. "
                    "Please ensure all nodes have content."
                )
        return nodes
    
    def _add_nodes_to_index(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
        **insert_kwargs: Any,
    ) -> None:
        """Add document to index."""
        if not nodes:
            print("No nodes to add, return empty index")
            return

        for nodes_batch in iter_batch(nodes, self._insert_batch_size):
            # validate nodes
            nodes_batch = self.is_validate_nodes(nodes_batch)
            # get embeddings
            nodes_batch = self._get_node_with_embedding(nodes_batch, show_progress)
            # insert to vector_store
            new_ids = self._vector_store.add(nodes_batch, **insert_kwargs)
            
            # NOTE: if the vector store doesn't store text,
            # we need to add the nodes to document store
            if not self._vector_store.stores_text:
                print("add the nodes to the document store")
                for node, _ in zip(nodes_batch, new_ids):
                    # NOTE: remove embedding from node to avoid duplication
                    node_without_embedding = node.copy()
                    node_without_embedding.embedding = None

                    self._storage_context.docstore.add_documents(
                        [node_without_embedding], allow_update=True
                    )

    def _get_node_with_embedding(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """Get tuples of id, node, and embedding.

        Allows us to store these nodes in a vector store.
        Embeddings are called in batches.

        """
        id_to_embed_map = self.embed_nodes(
            nodes, show_progress=show_progress
        )

        results = []
        for node in nodes:
            embedding = id_to_embed_map[node.node_id]
            result = node.copy()
            result.embedding = embedding
            results.append(result)
        return results

    async def _aget_node_with_embedding(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """Asynchronously get tuples of id, node, and embedding.

        Allows us to store these nodes in a vector store.
        Embeddings are called in batches.

        """
        id_to_embed_map = await self.async_embed_nodes(
            nodes=nodes,
            show_progress=show_progress,
        )

        results = []
        for node in nodes:
            embedding = id_to_embed_map[node.node_id]
            result = node.copy()
            result.embedding = embedding
            results.append(result)
        return results

    async def _async_add_nodes_to_index(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
        **insert_kwargs: Any,
    ) -> None:
        """Asynchronously add nodes to index."""
        if not nodes:
            return

        for nodes_batch in iter_batch(nodes, self._insert_batch_size):
            # validate nodes
            nodes_batch = self.is_validate_nodes(nodes_batch)
            # get embedddings
            nodes_batch = await self._aget_node_with_embedding(
                nodes_batch, show_progress
            )
            # add to vector store
            new_ids = await self._vector_store.async_add(nodes_batch, **insert_kwargs)

            # if the vector store doesn't store text, we need to add the nodes to the
            # index struct and document store
            if not self._vector_store.stores_text:
                for node, _ in zip(nodes_batch, new_ids):
                    # NOTE: remove embedding from node to avoid duplication
                    node_without_embedding = node.copy()
                    node_without_embedding.embedding = None

                    self._storage_context.docstore.add_documents(
                        [node_without_embedding], allow_update=True
                    )

    def embed_nodes(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False
    ) -> Dict[str, List[float]]:
        """Get embeddings of the given nodes, run embedding model if necessary.

        Args:
            nodes (Sequence[BaseNode]): The nodes to embed.
            embed_model (BaseEmbedding): The embedding model to use.
            show_progress (bool): Whether to show progress bar.

        Returns:
            Dict[str, List[float]]: A map from node id to embedding.
        """
        id_to_embed_map: Dict[str, List[float]] = {}

        texts_to_embed = []
        ids_to_embed = []

        for node in nodes:
            if node.embedding is None:
                ids_to_embed.append(node.node_id)
                texts_to_embed.append(node.get_content(metadata_mode=MetadataMode.EMBED))
            else:
                id_to_embed_map[node.node_id] = node.embedding

        new_embeddings = self._service_context.embed_model.get_text_embedding_batch(
            texts_to_embed, show_progress=show_progress
        )

        for new_id, text_embedding in zip(ids_to_embed, new_embeddings):
            id_to_embed_map[new_id] = text_embedding

        return id_to_embed_map

    async def async_embed_nodes(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False
    ) -> Dict[str, List[float]]:
        """Async get embeddings of the given nodes, run embedding model if necessary.

        Args:
            nodes (Sequence[BaseNode]): The nodes to embed.
            embed_model (BaseEmbedding): The embedding model to use.
            show_progress (bool): Whether to show progress bar.

        Returns:
            Dict[str, List[float]]: A map from node id to embedding.
        """
        id_to_embed_map: Dict[str, List[float]] = {}

        texts_to_embed = []
        ids_to_embed = []
        for node in nodes:
            if node.embedding is None:
                ids_to_embed.append(node.node_id)
                texts_to_embed.append(node.get_content(metadata_mode=MetadataMode.EMBED))
            else:
                id_to_embed_map[node.node_id] = node.embedding

        new_embeddings = await self._service_context.embed_model.aget_text_embedding_batch(
            texts_to_embed, show_progress=show_progress
        )

        for new_id, text_embedding in zip(ids_to_embed, new_embeddings):
            id_to_embed_map[new_id] = text_embedding

        return id_to_embed_map

