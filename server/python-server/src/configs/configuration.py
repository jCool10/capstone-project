from omegaconf import DictConfig

from src.utils.files import (
    create_directories
)
from .schema import (
    OtherConfig,
    MilvusConfig,
    CassandraConfig,
    SentenceSplitterConfig,
    RecursiveSplitterConfig,
    SbertConfig,
    CrossEmbeddingConfig,
    AsymRerankConfig,
    CohereRerankConfig
)

class ConfigurationManager: 
    def __init__(
        self, 
        config: DictConfig, 
    ) -> None:
        self.config = config
        self.other_config = self.get_orther_config()
        
        create_directories([self.other_config.artifacts_root])
    
    def get_milvus_config(self) -> MilvusConfig: 
        """create instace for vector store config"""
        milvus_config = MilvusConfig(
            **self.config.vector_store
        )
        return milvus_config
    
    def get_cassandra_config(self) -> CassandraConfig: 
        """create instace for vector store config"""
        cassandra_config = CassandraConfig(
            **self.config.vector_store
        )
        return cassandra_config
    
    
    def get_sentence_splitter_config(self) -> SentenceSplitterConfig: 
        """create instace for splitter config"""
        sentence_splitter_config = SentenceSplitterConfig(
            **self.config.splitter,
        )
        return sentence_splitter_config

    def get_recursive_splitter_config(self) -> RecursiveSplitterConfig: 
        """create instace for splitter config"""
        recursive_splitter_config = RecursiveSplitterConfig(
            **self.config.splitter
        )
        return recursive_splitter_config
     
    def get_cross_embed_config(self) -> CrossEmbeddingConfig:
        """create instace for cross embedding config"""
        embed_config = CrossEmbeddingConfig(
            **self.config.embedding,
        )
        return embed_config

    def get_sbert_embed_config(self) -> SbertConfig:
        """create instace for sentence embedding config"""
        embed_config = SbertConfig(
            **self.config.embedding
        )
        return embed_config
    
    def get_asym_rerank_config(self) -> AsymRerankConfig:
        asym_rerank_config = AsymRerankConfig(
            **self.config.rerank
        )
        return asym_rerank_config
    
    def get_cohere_config(self) -> CohereRerankConfig:
        cohere_config = CohereRerankConfig(
            **self.config.rerank
        )
        return cohere_config

    
    def get_orther_config(self) -> OtherConfig:
        """create instace for other config"""
        other_config = OtherConfig(
            artifacts_root= self.config.artifacts_root,
            file_data_path= self.config.file_data_path,
            language= self.config.language,
            use_async= self.config.use_async,
            show_progress= self.config.show_progress,
            vector_store_query_mode= self.config.vector_store_query_mode,
            store_nodes_override= self.config.store_nodes_override,
            insert_batch_size= self.config.insert_batch_size,
            similarity_top_k= self.config.similarity_top_k,
        )
        return other_config