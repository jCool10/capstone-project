import os
import time
from omegaconf import DictConfig
from hydra import compose, initialize_config_dir
from dataclasses import asdict
from tqdm.auto import tqdm

from src.core.storage_context import StorageContext
from src.core.service_context import ServiceContext
from src.node_parser.vi_normalizer import ViNormalizer
from src.node_parser.en_normalizer import EngNormalizer
from src.vector_stores.milvus import MilvusVectorStore
from src.engine.db_engine import DatabaseEngine
from src.embeddings.huggingface import CrossEncoder
from src.configs.configuration import ConfigurationManager
from src.node.base_node import MetadataMode

from src.reader.dir_reader import DirectoryReader

startTime_load = int(round(time.time() * 1000))

file_dir = os.path.abspath(os.curdir) + "/data/law_dataset/legal_docs_cleaned_v2"
reader = DirectoryReader(
    input_dir=file_dir,
    recursive=True,
    num_files_limit=10,
)

csv_files = reader.load_data()
if csv_files:
    print("Load pdf success")
    print(len(csv_files))

# using hydra to load config
initialize_config_dir(version_base=None, config_dir=os.path.abspath(os.curdir) +  "/configs/")
cfg: DictConfig = compose("config.yaml")
print(cfg)

# load manager
manager = ConfigurationManager(config=cfg)

milvus_config = manager.get_milvus_config()
encoder_config = manager.get_cross_embed_config()
other_config = manager.get_orther_config()


# cần 2 params and config: của milvus và index -> done
# normalizer
normalizer = ViNormalizer() if other_config.language == "vi" else EngNormalizer()

# encoder   
emb_model = CrossEncoder(
    qry_model_name=encoder_config.qry_model_name,
    psg_model_name=encoder_config.psg_model_name,
    token=encoder_config.token,
    device=encoder_config.device,
)

# service context
service_context = ServiceContext.from_defaults(
    embed_model=emb_model,
)

#TODO: build milvus vector from documents
milvus_vector_store = MilvusVectorStore(
    **asdict(milvus_config),
)

# construct index and customize storage context
storage_context = StorageContext.from_defaults(
    vector_store=milvus_vector_store,
    vectorstore_name=milvus_config.vectorstore_name,
)

data_ingestor = DatabaseEngine(
    insert_batch_size=other_config.insert_batch_size,
    callback_manager=service_context.callback_manager,
    service_context=service_context,
    storage_context=storage_context,
    name_vector_store=milvus_config.vectorstore_name,
)

endTime_load = int(round(time.time() * 1000))
print(f"Time for load pipeline: {endTime_load - startTime_load} ms")


##########
startTime_run= int(round(time.time() * 1000))

for text_node in tqdm(csv_files, desc="Normalizing scripts"):
    text_node.text = normalizer.normalize(text_node.text)

# is one
nodes = csv_files

# run engine
data_ingestor.run_engine(nodes=nodes, show_progress=True)
storage_context.persist()

endTime_run= int(round(time.time() * 1000))
print(f"Time for load pipeline: {endTime_run - startTime_run} ms")