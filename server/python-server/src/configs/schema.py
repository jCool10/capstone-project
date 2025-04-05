from typing import (
    Dict,
    Any,
    Optional,
    Union,
    List
)
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MilvusConfig:
    vectorstore_name: str
    embedding_dim: int
    host: str
    port: str
    address: str
    uri: str
    user: str
    embedding_field: str
    primary_field: str
    text_field: str
    consistency_level: str
    collection_name: str
    index_params: Dict[str, Union[str, Dict[str, Any]]]
    search_params: Dict[str, Union[str, Dict[str, Any]]]
    overwrite: bool

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CassandraConfig:
    vectorstore_name: str
    embedding_dim: int
    table: str
    session: Optional[Any] = None
    keyspace: Optional[str] = None
    ttl_seconds: Optional[int] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SentenceSplitterConfig:
    splitter_mode: str
    model_name_tokenizer: str
    separator: str
    chunk_size: int
    chunk_overlap: int
    paragraph_separator: str
    secondary_chunking_regex: str

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RecursiveSplitterConfig:
    splitter_mode: str
    model_name_tokenizer: str
    separator: str
    chunk_size: int
    chunk_overlap: int
    backup_separators: str

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SbertConfig:
    model_name: str
    tokenizer_name: str
    pooling: str
    max_length: int
    normalize: bool
    embedding_batch_size: int
    cache_folder: str
    trust_remote_code: bool

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CrossEmbeddingConfig:
    qry_model_name: str
    psg_model_name: str
    token: str
    proxies: str
    methods: str
    device: Union[List[int], int, str]
    embedding_batch_size: int
    pooling: str
    max_length: int
    normalize: bool

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AsymRerankConfig:
    model_name_or_path: Optional[Any] = None
    model: Optional[Any] = None
    tokenizer: Optional[Any] = None
    token: Optional[str] = None
    device: Optional[Union[str, int, List[int]]] = None
    methods: Optional[str] = 'huggingface'
    proxies: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CohereRerankConfig:
    top_n: int
    model: str
    api_key: str

@dataclass
class OtherConfig:
    # Path
    artifacts_root: str
    file_data_path: str
    # Normalizer
    language: str
    # General
    use_async: bool
    show_progress: bool
    # retriever
    vector_store_query_mode: str
    store_nodes_override: bool
    insert_batch_size: int
    similarity_top_k: int