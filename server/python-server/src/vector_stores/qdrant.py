import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from omegaconf import OmegaConf, DictConfig
from src.node.base_node import BaseNode, TextNode
from src.vector_stores import (
    MetadataFilters,
    VectorStore,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)

from .utils import (
    metadata_dict_to_node,
    node_to_metadata_dict,
    DEFAULT_DOC_ID_KEY,
    DEFAULT_EMBEDDING_KEY,
    DEFAULT_TEXT_KEY,
)

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

QDRANT_ID_FIELD = "id"


def _to_qdrant_filter(standard_filters: MetadataFilters) -> List[str]:
    """Translate standard metadata filters to Qdrant specific spec."""
    filters = []
    for filter in standard_filters.filters:
        if isinstance(filter.value, str):
            filters.append(f"{filter.key} == '{filter.value}'")
        else:
            filters.append(f"{filter.key} == {filter.value}")
    return filters


class QdrantVectorStore(VectorStore):
    """The Qdrant Vector Store.

    This vector store stores text, its embedding, and metadata in Qdrant.
    It allows the use of an existing collection or creating a new one if it does not exist.

    Args:
        uri (str, optional): The URI to connect to, typically "http://address:port".
        collection_name (str, optional): The name of the collection where data will be stored.
        embedding_dim (int, optional): The dimension of the embedding vectors for the collection.
        embedding_field (str, optional): The name of the embedding field for the collection.
        consistency_level (str, optional): The consistency level to use.
        overwrite (bool, optional): Whether to overwrite an existing collection with the same name.
        search_params (dict, optional): The search configuration for querying the collection.
        index_params (dict, optional): The index configuration for creating the collection.
    """

    stores_text: bool = True
    stores_node: bool = True

    def __init__(
        self,
        uri: str = "http://localhost:6333",
        collection_name: str = "qdrant_collection",
        embedding_dim: Optional[int] = None,
        embedding_field: str = DEFAULT_EMBEDDING_KEY,
        primary_field: str = DEFAULT_DOC_ID_KEY,
        text_field: Optional[str] = DEFAULT_TEXT_KEY,
        consistency_level: str = "Strong",
        overwrite: bool = False,
        search_params: Optional[Dict[str, Union[str, dict]]] = None,
        index_params: Optional[Dict[str, Union[str, dict]]] = None,
        **kwargs,
    ) -> None:
        import_err_msg = (
            "`qdrant-client` package not found, please run `pip install qdrant-client`"
        )
        try:
            import qdrant_client  # noqa
        except ImportError:
            raise ImportError(import_err_msg)

        from qdrant_client import QdrantClient

        self.uri = uri
        self.collection_name = collection_name
        self.dim = embedding_dim
        self.embedding_field = embedding_field
        self.doc_id_field = primary_field
        self.text_field = text_field
        self.consistency_level = consistency_level
        self.overwrite = overwrite

        # Resolve config if passing DictConfig of Omega to Qdrant
        if isinstance(search_params, DictConfig):
            search_params = OmegaConf.to_container(search_params, resolve=True)
        self.search_params = search_params
        if isinstance(index_params, DictConfig):
            index_params = OmegaConf.to_container(index_params, resolve=True)
        self.index_params = index_params

        # Connect to Qdrant instance
        self.qdrantclient = self.connect_client()

        # Delete collection if overwriting
        if (
            self.overwrite
            and self.collection_name in self.qdrantclient.get_collections()
        ):
            self.qdrantclient.delete_collection(self.collection_name)

        # Create the collection if it does not exist
        if self.collection_name not in self.qdrantclient.get_collections():
            if self.dim is None:
                raise ValueError("Dim argument required for collection creation.")
            self.qdrantclient.create_collection(
                collection_name=self.collection_name,
                vector_size=self.dim,
                distance="Cosine",
            )

        logger.debug(f"Successfully created a new collection: {self.collection_name}")

    def connect_client(self) -> "QdrantClient":
        from qdrant_client import QdrantClient

        return QdrantClient(self.uri)

    @property
    def client(self) -> Any:
        """Get client."""
        return self.qdrantclient

    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Add embeddings and their nodes into Qdrant."""
        insert_list = []
        insert_ids = []

        # Prepare the data to be inserted
        for node in nodes:
            entry = node_to_metadata_dict(node)
            entry[QDRANT_ID_FIELD] = node.node_id
            entry[self.embedding_field] = node.embedding
            entry["text"] = node.text

            insert_ids.append(node.node_id)
            insert_list.append(entry)

        # Insert the data into Qdrant
        self.qdrantclient.upsert(
            collection_name=self.collection_name,
            points=insert_list,
        )
        logger.debug(
            f"Successfully inserted embeddings into: {self.collection_name} "
            f"Num Inserted: {len(insert_list)}"
        )
        return insert_ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """Delete nodes using doc_id."""
        doc_ids = [ref_doc_id] if isinstance(ref_doc_id, str) else ref_doc_id
        self.qdrantclient.delete(
            collection_name=self.collection_name,
            points=doc_ids,
        )
        logger.debug(f"Successfully deleted embedding with doc_id: {doc_ids}")

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Query Qdrant for top k most similar nodes."""
        if query.mode != VectorStoreQueryMode.DEFAULT:
            raise ValueError(f"Qdrant does not support {query.mode} yet.")

        expr = []

        # Parse the filter
        if query.filters is not None:
            expr.extend(_to_qdrant_filter(query.filters))

        # Parse any nodes we are filtering on
        if query.node_ids is not None and len(query.node_ids) != 0:
            expr_list = [f"'{entry}'" for entry in query.node_ids]
            expr.append(f"{QDRANT_ID_FIELD} in [{','.join(expr_list)}]")

        # Perform the search
        res = self.qdrantclient.search(
            collection_name=self.collection_name,
            query_vector=query.query_embedding,
            filter=expr,
            limit=query.similarity_top_k,
            params=self.search_params,
        )

        nodes = []
        similarities = []
        ids = []

        # Parse the results
        for hit in res:
            if not self.text_field:
                node = metadata_dict_to_node(
                    {
                        "_node_content": hit.payload.get("_node_content", None),
                        "_node_type": hit.payload.get("_node_type", None),
                    }
                )
            else:
                try:
                    text = hit.payload.get(self.text_field)
                except Exception:
                    raise ValueError(
                        "The passed in text_key value does not exist in the retrieved entity."
                    )
                node = TextNode(text=text)
            nodes.append(node)
            similarities.append(hit.score)
            ids.append(hit.id)

        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)
