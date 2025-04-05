import logging 
from typing import Optional, List
import time
from dataclasses import asdict
from transformers import AutoTokenizer

from src.configs.schema import (
    MilvusConfig,
    SentenceSplitterConfig,
    OtherConfig,
    CrossEmbeddingConfig
)
from src.node.base_node import Document
from src.core.storage_context import StorageContext
from src.core.service_context import ServiceContext
from src.node_parser.vi_normalizer import ViNormalizer
from src.node_parser.en_normalizer import EngNormalizer
from src.node_parser.text.sentence import SentenceSplitter 
from src.vector_stores.milvus import MilvusVectorStore
from src.engine.db_engine import DatabaseEngine
from src.callbacks.callback_manager import CallbackManager
from src.embeddings.huggingface import CrossEncoder

logger = logging.getLogger(__name__)

class InitializeDatabase:
    def __init__(self,
        splitter_config: SentenceSplitterConfig,
        milvus_config: MilvusConfig,
        encoder_config: CrossEmbeddingConfig,
        other_config: OtherConfig,
    ) -> None:
        # config
        self.splitter_config = splitter_config
        self.milvus_config = milvus_config
        self.encoder_config = encoder_config
        self.other_config = other_config

        # callback manager
        self.callback_manager = CallbackManager()

        # node parser
        node_parser = self.get_node_parser(config=self.splitter_config)

        # normalizer
        self.normalizer = ViNormalizer() if self.other_config.language == "vi" else EngNormalizer()

        # encoder 
        self.emb_model = self.get_encoder(config=self.encoder_config)
    
        # service context
        self.service_context = ServiceContext.from_defaults(
            embed_model=self.emb_model,
            node_parser=node_parser,
            callback_manager=self.callback_manager,
        )

        #TODO: build milvus vector from documents
        milvus_vector_store = MilvusVectorStore(
            **asdict(self.milvus_config),
        )

        # construct index and customize storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=milvus_vector_store,
            vectorstore_name=self.milvus_config.vectorstore_name,
        )

    def main(self, documents: List[Document]):

        """Wrap time"""
        start_build_collection_index = int(round(time.time() * 1000))

        # Fisrt step: Normalize text
        for doc in documents:
            doc.text = self.normalizer.normalize(doc.text)

        nodes = []

        # parser = List[NodeParser]
        for each_parser in self.service_context.transformations: 
            parsing_nodes = each_parser.get_nodes_from_documents(
                documents=documents,
                show_progress=True,
            )
            nodes.extend(parsing_nodes)

        # TODO:
        # (1) Add build index from nodes to get embeddings
        data_ingestor = DatabaseEngine(
            insert_batch_size=self.other_config.insert_batch_size,
            callback_manager=self.callback_manager,
            service_context=self.service_context,
            storage_context=self.storage_context,
            name_vector_store=self.milvus_config.vectorstore_name,
        )

        data_ingestor.run_engine(nodes=nodes, show_progress=True)

        self.storage_context.persist()
        end_build_collection_index = int(round(time.time() * 1000))
        print(f"Time for build collection and index: {end_build_collection_index - start_build_collection_index} ms")

        return "Add success!!"

    
    def get_node_parser(self, config: SentenceSplitterConfig) -> SentenceSplitter:
        """create instace for node parser"""
        tokenizer = AutoTokenizer.from_pretrained(config.model_name_tokenizer)

        self.node_parser = SentenceSplitter(
            separator=config.separator,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            tokenizer=tokenizer.encode,
            paragraph_separator="\n\n\n",
            secondary_chunking_regex=config.secondary_chunking_regex,
            callback_manager=self.callback_manager,
        )
        return self.node_parser
    
    def get_encoder(self, config: CrossEmbeddingConfig) -> CrossEncoder:
        """create instace for cross embedding"""
        emb_model = CrossEncoder(
            qry_model_name=config.qry_model_name,
            psg_model_name=config.psg_model_name,
            token=config.token,
            device=config.device,
        )
        return emb_model