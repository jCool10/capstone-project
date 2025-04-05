#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAG Chatbot sử dụng kiến trúc modular
"""

import os
import sys
import time
import uuid
import argparse
from dataclasses import asdict
from tqdm import tqdm

# Import các thư viện cần thiết
from omegaconf import DictConfig
from hydra import compose, initialize_config_dir

from src.core.storage_context import StorageContext
from src.core.service_context import ServiceContext
from src.node_parser.vi_normalizer import ViNormalizer
from src.node_parser.en_normalizer import EngNormalizer
from src.vector_stores.milvus import MilvusVectorStore
from src.engine.db_engine import DatabaseEngine
from src.embeddings.huggingface import CrossEncoder
from src.configs.configuration import ConfigurationManager
from src.retriever.vector_retriever import VectorRetriever
from src.reranker.cross_encoder_reranker import CrossEncoderReranker
from src.reader.dir_reader import DirectoryReader
from src.node.base_node import MetadataMode


class RAGChatbot:
    """Chatbot sử dụng Retrieval-Augmented Generation (RAG)"""

    def __init__(self, retriever, reranker, llm_model_name="Mistral-7B-Instruct-v0.2"):
        """
        Khởi tạo RAG Chatbot

        Args:
            retriever: Đối tượng retriever để truy xuất tài liệu
            reranker: Đối tượng reranker để xếp hạng lại các kết quả
            llm_model_name: Tên mô hình ngôn ngữ lớn sử dụng
        """
        self.retriever = retriever
        self.reranker = reranker

        # Khởi tạo mô hình LLM
        print(f"Đang tải mô hình LLM {llm_model_name}...")

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            self.tokenizer = AutoTokenizer.from_pretrained(
                f"mistralai/{llm_model_name}"
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                f"mistralai/{llm_model_name}",
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            print("Đã tải xong mô hình LLM!")
            self.model_loaded = True

        except Exception as e:
            print(f"Lỗi khi tải mô hình: {e}")
            print("Sẽ sử dụng văn bản truy xuất trực tiếp làm câu trả lời.")
            self.model_loaded = False

    def retrieve_context(self, query, verbose=False):
        """
        Truy xuất văn bản liên quan từ cơ sở dữ liệu

        Args:
            query: Câu truy vấn
            verbose: Hiển thị thông tin chi tiết

        Returns:
            context: Văn bản ngữ cảnh đã kết hợp
            reranked_nodes: Các node sau khi xếp hạng lại
        """
        # Lấy kết quả từ retriever
        retrieved_nodes = self.retriever.retrieve(query)

        # Sử dụng reranker để xếp hạng lại kết quả
        if self.reranker and len(retrieved_nodes) > 0:
            reranked_nodes = self.reranker.rerank(query, retrieved_nodes)
        else:
            reranked_nodes = retrieved_nodes

        # Kết hợp các văn bản
        context = "\n\n".join([node.get_text() for node in reranked_nodes])

        if verbose:
            print(f"Số lượng node truy xuất: {len(retrieved_nodes)}")
            print(f"Số lượng node sau khi xếp hạng lại: {len(reranked_nodes)}")
            print("\nNguồn tài liệu truy xuất:")
            for i, node in enumerate(reranked_nodes):
                print(f"{i+1}. {node.metadata.get('file_path', 'Unknown')}")

        return context, reranked_nodes

    def generate_response(self, query, context):
        """
        Tạo câu trả lời dựa trên truy vấn và ngữ cảnh

        Args:
            query: Câu truy vấn
            context: Ngữ cảnh truy xuất được

        Returns:
            response: Câu trả lời được tạo
        """
        if not self.model_loaded:
            return f"Kết quả truy xuất:\n\n{context}"

        # Tạo prompt cho mô hình
        prompt = f"""<s>[INST] Bạn là một trợ lý AI hữu ích và chính xác. Sử dụng thông tin từ các đoạn sau để trả lời câu hỏi. 
Nếu thông tin không có trong đoạn văn bản, hãy nói rằng bạn không có đủ thông tin để trả lời.

Thông tin tham khảo:
{context}

Câu hỏi: {query} [/INST]</s>"""

        import torch

        # Mã hóa prompt
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        # Tạo đầu ra
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Giải mã đầu ra
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        return response

    def chat(self, query, verbose=False):
        """
        Xử lý truy vấn và tạo câu trả lời sử dụng RAG

        Args:
            query: Câu truy vấn
            verbose: Hiển thị thông tin chi tiết

        Returns:
            response: Câu trả lời
        """
        # Truy xuất ngữ cảnh
        context, nodes = self.retrieve_context(query, verbose=verbose)

        # Tạo câu trả lời
        if not context.strip():
            return "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu."

        response = self.generate_response(query, context)
        return response


def create_sample_data(sample_dir="sample_data"):
    """
    Tạo dữ liệu mẫu để demo

    Args:
        sample_dir: Thư mục chứa dữ liệu mẫu
    """
    # Tạo thư mục sample_data nếu chưa tồn tại
    os.makedirs(sample_dir, exist_ok=True)

    # Tạo một số tài liệu mẫu
    documents = [
        {
            "filename": "python_intro.txt",
            "content": """Python là một ngôn ngữ lập trình bậc cao, có cú pháp rõ ràng, dễ đọc. 
Python hỗ trợ nhiều mô hình lập trình như hướng đối tượng, lập trình chức năng và lập trình thủ tục.
Python được phát triển bởi Guido van Rossum vào cuối những năm 1980 và được phát hành lần đầu vào năm 1991.
Python có thư viện chuẩn rộng lớn, cung cấp các công cụ phù hợp cho nhiều tác vụ.""",
        },
        {
            "filename": "java_intro.txt",
            "content": """Java là một ngôn ngữ lập trình hướng đối tượng được phát triển bởi Sun Microsystems vào năm 1995.
Java tuân theo triết lý 'viết một lần, chạy mọi nơi', nghĩa là mã Java có thể chạy trên tất cả các nền tảng hỗ trợ Java.
Java có cú pháp tương tự như C++ nhưng thiết kế đơn giản hơn và loại bỏ các tính năng cấp thấp.""",
        },
        {
            "filename": "ml_intro.txt",
            "content": """Machine Learning (Học máy) là một lĩnh vực của trí tuệ nhân tạo tập trung vào phát triển các thuật toán giúp máy tính học từ dữ liệu.
Học máy có thể được phân loại thành ba loại chính: học có giám sát, học không giám sát và học tăng cường.
Trong học có giám sát, mô hình được huấn luyện trên dữ liệu có nhãn trong khi học không giám sát làm việc với dữ liệu không có nhãn.
Học tăng cường tập trung vào cách tác nhân nên hành động trong một môi trường để tối đa hóa phần thưởng tích lũy.""",
        },
        {
            "filename": "nlp_intro.txt",
            "content": """Xử lý ngôn ngữ tự nhiên (NLP) là một lĩnh vực của trí tuệ nhân tạo liên quan đến tương tác giữa máy tính và ngôn ngữ con người.
NLP kết hợp các phương pháp từ khoa học máy tính, trí tuệ nhân tạo và ngôn ngữ học.
Các ứng dụng NLP bao gồm phân tích văn bản, nhận dạng giọng nói, dịch máy và chatbot.
Các kỹ thuật NLP hiện đại thường sử dụng học sâu và mô hình ngôn ngữ lớn (LLM) như BERT, GPT và T5.""",
        },
        {
            "filename": "rag_intro.txt",
            "content": """Retrieval-Augmented Generation (RAG) là một kiến trúc hybrid kết hợp hệ thống truy xuất với mô hình ngôn ngữ lớn (LLM).
Trong RAG, một truy vấn đầu tiên được sử dụng để truy xuất tài liệu liên quan từ kho kiến thức bên ngoài.
Các tài liệu truy xuất và truy vấn ban đầu sau đó được kết hợp và gửi đến LLM để tạo câu trả lời.
RAG giúp cải thiện độ chính xác của câu trả lời, giảm hiện tượng ảo giác (hallucination) và cho phép LLM truy cập kiến thức mới hơn, chuyên biệt hơn.
Các hệ thống RAG modular cho phép tùy chỉnh và tối ưu hóa từng thành phần trong pipeline như bộ nhúng, bộ truy xuất và bộ tái xếp hạng.""",
        },
    ]

    # Ghi các tài liệu vào thư mục sample_data
    for doc in documents:
        with open(
            os.path.join(sample_dir, doc["filename"]), "w", encoding="utf-8"
        ) as f:
            f.write(doc["content"])

    print(f"Đã tạo {len(documents)} tài liệu mẫu trong thư mục '{sample_dir}'")


def setup_rag_components(sample_dir="sample_data"):
    """
    Thiết lập các thành phần của hệ thống RAG

    Args:
        sample_dir: Thư mục chứa dữ liệu mẫu

    Returns:
        chatbot: Đối tượng RAGChatbot đã được khởi tạo
        collection_name: Tên collection trong Milvus
        milvus_vector_store: Vector store Milvus
    """
    # Khởi tạo và tải cấu hình
    config_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "configs")
    )
    initialize_config_dir(version_base=None, config_dir=config_dir)
    cfg: DictConfig = compose("config.yaml")

    # Tạo configuration manager
    manager = ConfigurationManager(config=cfg)

    # Lấy các cấu hình cụ thể
    milvus_config = manager.get_milvus_config()
    encoder_config = manager.get_cross_embed_config()
    other_config = manager.get_orther_config()
    reranker_config = manager.get_reranker_config()

    print("Đã tải cấu hình thành công!")

    # Đọc tài liệu từ thư mục mẫu
    reader = DirectoryReader(input_dir=sample_dir, recursive=True)

    # Tải dữ liệu
    text_nodes = reader.load_data()
    print(f"Đã tải {len(text_nodes)} tài liệu.")

    # Chuẩn hóa văn bản
    normalizer = EngNormalizer() if other_config.language == "en" else ViNormalizer()
    for text_node in tqdm(text_nodes, desc="Đang chuẩn hóa văn bản"):
        text_node.text = normalizer.normalize(text_node.text)

    print("Đã hoàn thành việc chuẩn hóa văn bản!")

    # Đặt tên collections cho demo
    collection_name = f"rag_chatbot_demo_{uuid.uuid4().hex[:8]}"
    milvus_config.collection = collection_name
    milvus_config.vectorstore_name = collection_name

    # Khởi tạo mô hình embedding
    embed_model = CrossEncoder(
        qry_model_name=encoder_config.qry_model_name,
        psg_model_name=encoder_config.psg_model_name,
        token=encoder_config.token,
        device=encoder_config.device,
    )

    # Tạo service context
    service_context = ServiceContext.from_defaults(
        embed_model=embed_model,
    )

    # Tạo kho lưu trữ vector Milvus
    milvus_vector_store = MilvusVectorStore(
        **asdict(milvus_config),
    )

    # Tạo storage context
    storage_context = StorageContext.from_defaults(
        vector_store=milvus_vector_store,
        vectorstore_name=milvus_config.vectorstore_name,
    )

    print(f"Đã thiết lập các thành phần với collection name: {collection_name}")

    # Tạo database engine
    data_ingestor = DatabaseEngine(
        insert_batch_size=other_config.insert_batch_size,
        callback_manager=service_context.callback_manager,
        service_context=service_context,
        storage_context=storage_context,
        name_vector_store=milvus_config.vectorstore_name,
    )

    # Chạy engine để nhập dữ liệu
    print("Bắt đầu nhập dữ liệu vào cơ sở dữ liệu vector...")
    start_time = time.time()
    data_ingestor.run_engine(nodes=text_nodes, show_progress=True)
    storage_context.persist()
    end_time = time.time()
    print(f"Đã hoàn thành việc nhập dữ liệu trong {end_time - start_time:.2f} giây.")

    # Khởi tạo vector retriever
    retriever = VectorRetriever(
        vector_store=milvus_vector_store,
        embed_model=embed_model,
        name_vector_store=milvus_config.vectorstore_name,
        top_k=reranker_config.top_k,
    )

    # Khởi tạo reranker
    reranker = CrossEncoderReranker(
        top_n=reranker_config.top_n,
        model=reranker_config.model,
        tokenizer=reranker_config.tokenizer,
    )

    print("Đã khởi tạo các thành phần RAG thành công!")

    # Khởi tạo chatbot
    chatbot = RAGChatbot(retriever, reranker)

    return chatbot, collection_name, milvus_vector_store


def start_gradio_interface(chatbot):
    """
    Khởi động giao diện Gradio

    Args:
        chatbot: Đối tượng RAGChatbot
    """
    try:
        import gradio as gr
    except ImportError:
        print(
            "Thư viện Gradio chưa được cài đặt. Cài đặt bằng lệnh: pip install gradio"
        )
        return

    def respond_to_query(query, show_sources=False):
        if not query.strip():
            return "Vui lòng nhập câu hỏi.", ""

        # Truy xuất ngữ cảnh
        context, nodes = chatbot.retrieve_context(query, verbose=False)

        # Tạo câu trả lời
        if not context.strip():
            return "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu.", ""

        response = chatbot.generate_response(query, context)

        # Hiển thị nguồn nếu được yêu cầu
        sources = ""
        if show_sources and nodes:
            sources = "**Nguồn tài liệu:**\n"
            for i, node in enumerate(nodes):
                file_path = node.metadata.get("file_path", "Unknown")
                if isinstance(file_path, str) and os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    sources += f"{i+1}. {file_name}\n"

        return response, sources

    # Tạo giao diện Gradio
    with gr.Blocks(title="RAG Chatbot Demo") as demo:
        gr.Markdown("# RAG Chatbot Demo")
        gr.Markdown(
            "Chatbot sử dụng Retrieval-Augmented Generation (RAG) với dữ liệu của bạn."
        )

        with gr.Row():
            with gr.Column(scale=4):
                query_input = gr.Textbox(
                    label="Câu hỏi", placeholder="Nhập câu hỏi của bạn..."
                )
                show_sources = gr.Checkbox(label="Hiển thị nguồn tài liệu", value=True)
                submit_btn = gr.Button("Gửi")

        with gr.Row():
            with gr.Column(scale=4):
                response_output = gr.Markdown(label="Trả lời")
                sources_output = gr.Markdown(label="Nguồn")

        submit_btn.click(
            fn=respond_to_query,
            inputs=[query_input, show_sources],
            outputs=[response_output, sources_output],
        )
        query_input.submit(
            fn=respond_to_query,
            inputs=[query_input, show_sources],
            outputs=[response_output, sources_output],
        )

    # Khởi chạy giao diện
    demo.launch(share=True)


def cleanup_resources(milvus_vector_store, collection_name):
    """
    Dọn dẹp tài nguyên

    Args:
        milvus_vector_store: Vector store Milvus
        collection_name: Tên collection
    """
    try:
        # Xóa collection trong Milvus
        milvus_vector_store.delete_collection()
        print(f"Đã xóa collection {collection_name} từ Milvus.")
    except Exception as e:
        print(f"Lỗi khi xóa collection: {e}")


def chat_cli(chatbot):
    """
    Giao diện dòng lệnh để tương tác với chatbot

    Args:
        chatbot: Đối tượng RAGChatbot
    """
    print("\n===== RAG Chatbot CLI =====")
    print("Nhập 'exit' hoặc 'quit' để thoát.")

    while True:
        query = input("\n[Bạn]: ")

        if query.lower() in ["exit", "quit"]:
            print("Kết thúc chat. Tạm biệt!")
            break

        if not query.strip():
            continue

        print("\n[Đang xử lý...]")
        start_time = time.time()
        response = chatbot.chat(query, verbose=True)
        end_time = time.time()

        print(f"\n[Chatbot] ({end_time - start_time:.2f}s):")
        print(response)


def main():
    """Hàm chính để chạy chương trình"""

    # Phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(
        description="RAG Chatbot sử dụng kiến trúc modular"
    )
    parser.add_argument("--ui", action="store_true", help="Khởi động giao diện Gradio")
    parser.add_argument("--create-data", action="store_true", help="Tạo dữ liệu mẫu")
    parser.add_argument(
        "--data-dir", type=str, default="sample_data", help="Thư mục chứa dữ liệu"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Dọn dẹp tài nguyên sau khi hoàn thành"
    )

    args = parser.parse_args()

    # Tạo dữ liệu mẫu nếu cần
    if args.create_data:
        create_sample_data(args.data_dir)

    # Thiết lập các thành phần RAG
    chatbot, collection_name, milvus_vector_store = setup_rag_components(args.data_dir)

    # Chạy giao diện hoặc CLI
    if args.ui:
        try:
            start_gradio_interface(chatbot)
        except KeyboardInterrupt:
            print("\nĐã dừng giao diện Gradio.")
    else:
        try:
            chat_cli(chatbot)
        except KeyboardInterrupt:
            print("\nĐã dừng chatbot.")

    # Dọn dẹp tài nguyên nếu được chỉ định
    if args.cleanup:
        cleanup_resources(milvus_vector_store, collection_name)


if __name__ == "__main__":
    main()
