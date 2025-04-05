import gradio as gr
from omegaconf import DictConfig
from hydra import compose, initialize_config_dir
import time
import os

from src.pipeline.milvus_retrieve import MilvusRetrieverPipeline
from src.configs.configuration import ConfigurationManager
from src.node.base_node import MetadataMode

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

##########
# Gradio #
##########

def retrieve(query_user: str):
    # Call pipeline
    nodes_retrieve, nodes_rerank = retriever_pipeline.main(
            query=query_user,
        )
    
    # Format text to display
    format_nodes_retrieve = []
    for node in nodes_retrieve:
        text = node.get_content(metadata_mode=MetadataMode.ALL).strip()
        score = node.score
        format_nodes_retrieve.append(
            f"Text:\n'''{text}'''\nScore:{score}"
        )
        format_nodes_retrieve.append("\n" + "-" * 20 + "\n")

    format_nodes_rerank=[]
    for node in nodes_rerank:
        format_nodes_rerank.append(
            f"Text:\n'''{node['text_bundle']}'''\nScore:{node['score'].item()}"
        )
        format_nodes_rerank.append("\n" + "-" * 20 + "\n")

    return "".join(format_nodes_retrieve), "".join(format_nodes_rerank) 

with gr.Blocks() as demo:
    with gr.Row():
        input_query = gr.Textbox(None, label="User Query")
    with gr.Row():
        trans_button = gr.Button("Run")


    with gr.Row():
        with gr.Column():
            retrieve_result = gr.Textbox(None, label="Retrieve Result")
        with gr.Column():
            rerank_result = gr.Textbox(None, label="Rerank Result")

    input_list = [
        input_query
    ]
        
    trans_button.click(fn=retrieve, inputs=input_list, outputs=[retrieve_result, rerank_result])

demo.launch(share=True, debug=True)
