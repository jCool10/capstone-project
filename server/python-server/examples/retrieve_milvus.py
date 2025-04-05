from pathlib import Path
import time
import os
from omegaconf import DictConfig
from hydra import compose, initialize_config_dir

from src.pipeline.milvus_retrieve import MilvusRetrieverPipeline
from src.configs.configuration import ConfigurationManager

# ------------------
startTime_load = int(round(time.time() * 1000))

# using hydra to load config
initialize_config_dir(version_base=None, config_dir=os.path.abspath(os.curdir) +  "/configs/")
cfg: DictConfig = compose("config.yaml")
print(cfg)
# ------------------

# load manager
manager = ConfigurationManager(config=cfg)

asym_rerank_config = manager.get_asym_rerank_config()
milvus_config = manager.get_milvus_config()
encoder_config = manager.get_cross_embed_config()
other_config = manager.get_orther_config()


# cần 2 params and config: của milvus và index -> done
retriever_pipeline = MilvusRetrieverPipeline(
    milvus_config=milvus_config,
    encoder_config=encoder_config,
    other_config=other_config,
    asym_config=asym_rerank_config,
)

endTime_load = int(round(time.time() * 1000))
print(f"Time for load pipeline: {endTime_load - startTime_load} ms")

while True:
    # Main
    query_user = input("Input: ")
    startTime = int(round(time.time() * 1000))
    nodes, rerank_nodes = retriever_pipeline.main(
        query=query_user,
    )
    for node in nodes:
        # print("-" * 20)
        # text = node.get_content().strip()
        # metadata_info = node.node.get_metadata_str()
        # score = node.score
        # print( f"Node ID:{node.node_id}\nMETADATA\n:{metadata_info}\nText:\n'''{text}'''\nScore:{score}")
        print(node)
        print("\n\n")
    endTime = int(round(time.time() * 1000))
    print(f"Time for retriever_pipeline: {endTime - startTime} ms")
