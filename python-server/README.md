# RAG PDF Services

Dự án này là một hệ thống xử lý và truy xuất thông tin từ tài liệu PDF sử dụng kỹ thuật Retrieval-Augmented Generation (RAG).

## Cấu trúc dự án

```
.
├── configs/            # Cấu hình cho các thành phần khác nhau
│   ├── db/             # Cấu hình cơ sở dữ liệu (Milvus, FAISS, etc.)
│   ├── embedding/      # Cấu hình cho các mô hình embedding
│   ├── llm/            # Cấu hình cho các Large Language Models
│   ├── rerank/         # Cấu hình cho reranking
│   ├── retriever/      # Cấu hình cho các retriever
│   └── splitter/       # Cấu hình cho việc chia nhỏ văn bản
│
├── data/               # Thư mục chứa dữ liệu (tài liệu PDF, etc.)
│
├── examples/           # Ví dụ mẫu sử dụng
│
├── utils/              # Thư viện chính của dự án
│   ├── callbacks/      # Các callback handler
│   ├── config/         # Định nghĩa cấu trúc dữ liệu config
│   ├── constants/      # Các hằng số
│   ├── core/           # Các thành phần cốt lõi
│   ├── embeddings/     # Các mô hình embedding
│   ├── engine/         # Query engine
│   ├── indices/        # Chỉ mục cho việc truy xuất
│   ├── llm/            # Các mô hình ngôn ngữ lớn
│   ├── node/           # Xử lý node
│   ├── node_parser/    # Parser cho việc chia nhỏ văn bản
│   ├── output_parser/  # Parser cho đầu ra
│   ├── pipeline/       # Các pipeline xử lý
│   ├── prompt/         # Mẫu prompt
│   ├── rag_utils/      # Công cụ hỗ trợ RAG
│   ├── reader/         # Đọc các loại tài liệu
│   ├── rerank/         # Reranking kết quả
│   ├── retrievers/     # Các retriever
│   ├── schema/         # Định nghĩa schema
│   ├── storage/        # Lưu trữ
│   ├── synthesizer/    # Tổng hợp kết quả
│   ├── tools/          # Các công cụ tiện ích
│   └── vector_stores/  # Lưu trữ vector
│
└── setup.py            # Cấu hình cài đặt package
```

## Hướng dẫn sử dụng các thành phần chính

### 1. Cấu hình (configs/)

Thư mục này chứa các file cấu hình YAML cho các thành phần khác nhau của hệ thống:

```bash
# File config chính
configs/config.yaml

# Các config cho từng thành phần cụ thể
configs/splitter/    # Cấu hình chia nhỏ văn bản
configs/retriever/   # Cấu hình cho bộ truy xuất
configs/embedding/   # Cấu hình cho mô hình embedding
configs/db/          # Cấu hình cho cơ sở dữ liệu vector (Milvus, FAISS)
configs/llm/         # Cấu hình cho mô hình ngôn ngữ
```

### 2. Đọc dữ liệu (utils/reader/)

Thư mục này chứa các lớp để đọc dữ liệu từ các nguồn khác nhau:

```python
from utils.reader.directory_reader import DirectoryReader

# Đọc các file PDF từ thư mục
reader = DirectoryReader(input_files=["path/to/file1.pdf", "path/to/file2.pdf"])
# Hoặc đọc từ một thư mục
reader = DirectoryReader(input_dir="data/", required_exts=[".pdf"])
documents = reader.load_data()
```

### 3. Pipeline xử lý (utils/pipeline/)

Thư mục này chứa các pipeline hoàn chỉnh cho quá trình RAG:

```python
from utils.pipeline.milvus_retriever import MilvusRetrieverPipeline
from utils.config.configuration import ConfigurationManager

# Khởi tạo config manager
manager = ConfigurationManager(config_filepath="configs/config.yaml")

# Lấy cấu hình cho các thành phần
node_parser_config = manager.get_splitter_config()
milvus_config = manager.get_milvus_config()
embed_config = manager.get_embed_config()
index_retriever_config = manager.get_index_retriever_config()
response_config = manager.get_response_config()

# Khởi tạo pipeline
pipeline = MilvusRetrieverPipeline(
    splitter_config=node_parser_config,
    milvus_config=milvus_config,
    index_retriver_config=index_retriever_config,
    embed_config=embed_config,
    response_config=response_config,
)

# Sử dụng pipeline
results = pipeline.main(query="Câu truy vấn của bạn", documents=documents)
```

### 4. Vector store (utils/vector_stores/)

Các lớp quản lý lưu trữ vector:

```python
from utils.vector_stores.milvus import MilvusVectorStore
from utils.config.schema import MilvusConfig

# Tạo cấu hình cho Milvus
milvus_config = MilvusConfig(
    uri="localhost",
    port="19530",
    collection_name="my_collection"
)

# Khởi tạo vector store
vector_store = MilvusVectorStore(milvus_config)
```

### 5. Chia nhỏ văn bản (utils/node_parser/)

Các lớp để chia nhỏ tài liệu thành các đoạn:

```python
from utils.node_parser import SentenceSplitter
from transformers import AutoTokenizer

# Tạo tokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Khởi tạo splitter
splitter = SentenceSplitter(
    separator=".",
    chunk_size=512,
    chunk_overlap=50,
    tokenizer=tokenizer.encode
)

# Chia văn bản
nodes = splitter.get_nodes_from_documents(documents)
```

### 6. Embedding model (utils/embeddings/)

Các mô hình embedding để chuyển đổi văn bản thành vector:

```python
from utils.embeddings.huggingface import HuggingFaceEmbedding

# Khởi tạo embedding model
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    max_length=512
)

# Tạo embedding cho văn bản
embedding = embed_model.get_text_embedding("Văn bản cần embedding")
```

### 7. Retriever (utils/retrievers/)

Các lớp truy xuất thông tin:

```python
from utils.retrievers.dense.vector_retriver import VectorIndexRetriever

# Khởi tạo retriever với index đã tạo
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5
)

# Truy xuất thông tin
nodes = retriever.retrieve("Câu truy vấn")
```

## 🚀 Quick Start - RAG Evaluation

### Chạy đánh giá RAG hoàn chỉnh (Khuyến nghị):

```bash
# Khởi động Milvus trước
sudo docker compose up -d

# Chạy evaluation pipeline hoàn chỉnh (embed data + evaluate)
python run_evaluation.py
```

Pipeline này sẽ tự động:
- ✅ Kiểm tra và embed data từ `data/sample_documents.txt`
- ✅ Đánh giá 3 phương pháp: Dense, Sparse, Hybrid search
- ✅ So sánh hiệu suất và lưu kết quả
- ✅ In summary chi tiết

### Hoặc chạy với tùy chọn nâng cao:

```bash
# Chạy với collection tùy chỉnh
python evaluation/rag_evaluator.py --collection my_collection --data data/my_documents.txt

# Force re-embed data
python evaluation/rag_evaluator.py --force-reembed

# Sử dụng ground truth khác
python evaluation/rag_evaluator.py --ground-truth data/my_ground_truth.json
```

📋 **Xem hướng dẫn chi tiết**: [evaluation/COMPLETE_EVALUATION_GUIDE.md](evaluation/COMPLETE_EVALUATION_GUIDE.md)

## Cài đặt và chạy

### Cài đặt môi trường:

```bash
# Tạo môi trường ảo
conda create -n rag python=3.10 -y
conda activate rag

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt
```

### Cài đặt Milvus (nếu sử dụng vector store Milvus):

```bash
# Tải file cấu hình docker
wget https://github.com/milvus-io/milvus/releases/download/v2.3.2/milvus-standalone-docker-compose.yml -O docker-compose.yml

# Khởi động Milvus
sudo docker-compose up -d
```

### Chạy ví dụ:

```bash
# Chạy ví dụ mẫu
python examples/example_1.py
```

## Hỗ trợ các loại pipeline:

1. BM25 - Truy xuất dựa trên từ khóa
2. Decompose using Milvus vector - Phân rã câu hỏi và tìm kiếm vector
3. Dense retriever using Milvus - Truy xuất đặc trưng dày đặc sử dụng Milvus
4. Keyword retriever - Trích xuất từ khóa từ câu hỏi và so sánh với tài liệu

# RAG Pipeline Example

This project demonstrates a complete Retrieval-Augmented Generation (RAG) pipeline with the following components:

1. **User + Query and Documents inputs**: Loading documents and handling user queries
2. **Pre-Retrieval processing**: Text preprocessing using NLP techniques
3. **Indexing of documents**: Converting documents to vector embeddings and building a FAISS index
4. **Retrieval**: Finding the most relevant documents for a given query
5. **Post-Retrieval processing**: Preparing retrieved documents for LLM consumption
6. **Prompt + LLM integration**: Creating effective prompts and integrating with OpenAI
7. **Output generation**: Generating final responses with source attribution

## Requirements

```
nltk==3.8.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4
openai==0.28.1
python-dotenv==1.0.0
numpy==1.24.3
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the example:

```
python rag_pipeline_example.py
```

## Customize

To use your own documents, modify the `sample_documents` list in the example or create a function to load documents from files.

To change the LLM model or parameters, modify the `query_llm` method in the `RAGPipeline` class.

## Pipeline Overview

- **Document Loading**: The pipeline starts by loading documents into memory.
- **Preprocessing**: Documents are preprocessed by removing special characters, lemmatizing words, and removing stopwords.
- **Indexing**: Documents are converted to vector embeddings using Sentence Transformers and indexed using FAISS.
- **Retrieval**: When a query is received, it's processed the same way as documents, and the most similar documents are retrieved.
- **Post-Processing**: Retrieved documents are formatted with their metadata for LLM consumption.
- **Prompt Generation**: A prompt is constructed with the query and context from retrieved documents.
- **LLM Integration**: The prompt is sent to OpenAI's API to generate a response.
- **Output Generation**: The final response includes the answer, source documents, and metadata.