import logging
from typing import Optional

from src.vector_stores.base_vector import VectorStoreQueryResult
from src.utils.utils import truncate_text

_logger = logging.getLogger(__name__)

def log_vector_store_query_result(
    result: VectorStoreQueryResult, logger: Optional[logging.Logger] = None
) -> None:
    """Log vector store query result."""
    logger = logger or _logger

    assert result.ids is not None
    assert result.nodes is not None
    similarities = (
        result.similarities
        if result.similarities is not None and len(result.similarities) > 0
        else [1.0 for _ in result.ids]
    )

    fmt_txts = []
    for node_idx, node_similarity, node in zip(result.ids, similarities, result.nodes):
        fmt_txt = f"> [Node {node_idx}] [Similarity score: \
            {float(node_similarity):.6}] {truncate_text(node.get_content(), 100)}"
        fmt_txts.append(fmt_txt)
    top_k_node_text = "\n".join(fmt_txts)
    logger.debug(f"> Top {len(result.nodes)} nodes:\n{top_k_node_text}")