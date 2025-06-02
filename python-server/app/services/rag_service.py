import sys
import os

# Add the project root directory to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from typing import Dict, Any, List
from core.text_splitters.sentence_splitter import SentenceSplitter
from core.vector_stores.milvus import MilvusVectorStore
from core.document_loaders.file_loader import FileLoader
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, max_workers: int = 4):
        self.config = self._load_config()
        self.splitter = SentenceSplitter(
            chunk_size=self.config["document_processing"]["chunk_size"],
            chunk_overlap=self.config["document_processing"]["chunk_overlap"],
        )
        self.vector_store = MilvusVectorStore(
            uri=self.config["vector_store"]["uri"],
            embedding_name=self.config["vector_store"]["embedding_name"],
        )
        self.max_workers = max_workers  # Maximum number of threads

    def _load_config(self, config_path: str = "config.yaml") -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def _embed_document(self, file_path: str, collection_name: str) -> Dict[str, Any]:
        """Embed a document and add it to the collection.

        Args:
            file_path: Path to the file to be embedded
            collection_name: Name of the Milvus collection

        Returns:
            Dictionary containing the embedding results
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return {
                    "code": 400,
                    "success": False,
                    "message": "File does not exist",
                    "data": None,
                }

            loader = FileLoader(
                file_path=file_path,
            )
            documents = loader.load()

            if not documents:
                logger.warning(f"Could not load document from: {file_path}")
                return {
                    "code": 400,
                    "success": False,
                    "message": "Could not load document",
                    "data": None,
                }

            chunks = self.splitter.split_documents(documents)

            if not chunks:
                logger.warning(f"Could not split document into chunks: {file_path}")
                return {
                    "code": 400,
                    "success": False,
                    "message": "Could not split document into chunks",
                    "data": None,
                }

            result = self.vector_store.add(chunks, collection_name)

            if result:
                return {
                    "success": True,
                    "code": 200,
                    "message": "Documents embedded successfully",
                    "data": result,
                }
            else:
                return {
                    "success": False,
                    "code": 500,
                    "message": "Failed to embed documents",
                    "data": None,
                }

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {"code": 500, "success": False, "message": str(e), "data": None}

    def embed_documents(self, file_paths: List[str], collection_name: str):
        """Embed multiple documents in parallel using multithreading.

        Args:
            file_paths: List of paths to files for embedding
            collection_name: Name of the Milvus collection

        Returns:
            Dictionary containing the embedding results
        """
        if not file_paths:
            return {
                "code": 400,
                "success": False,
                "message": "No files provided",
                "data": None,
            }

        total_files = len(file_paths)
        logger.info(
            f"Starting embedding {total_files} files into collection {collection_name} with {self.max_workers} threads"
        )

        results = []
        successful = 0
        failed = 0

        # Determine optimal number of workers (no more than number of files)
        workers = min(self.max_workers, total_files)

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Create futures for each file
            futures = {
                executor.submit(
                    self._embed_document, file_path, collection_name
                ): file_path
                for file_path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(futures):
                res = future.result()
                results.append(res)
                if res["success"]:
                    successful += 1
                else:
                    failed += 1

        logger.info(
            f"Completed embedding {total_files} files. Success: {successful}, Failed: {failed}"
        )

        return {
            "code": 200,
            "success": True,
            "message": "Documents embedded successfully",
            "data": results,
        }

    def _create_prompt_from_docs(self, query: str, docs: List[Dict]) -> str:
        """Create a prompt from retrieved documents for LLM processing.

        Args:
            query: The original user query
            docs: List of retrieved documents

        Returns:
            Formatted prompt string for LLM
        """
        context_parts = []

        # Extract content from retrieved documents
        for i, doc in enumerate(docs):
            content = doc.get("text", "")

            if content:
                # Add document with source info
                context_parts.append(f"Document {i+1}:\n{content}\n")

        # Combine all documents into a single context
        context = "\n".join(context_parts)

        # Create the prompt with instructions, context and query
        prompt = f"""Dưới đây là một số đoạn văn bản liên quan đến câu hỏi của người dùng. 
Hãy sử dụng thông tin trong các đoạn văn này để trả lời câu hỏi.
Nếu không tìm thấy thông tin trong các đoạn văn, hãy cho biết bạn không có đủ thông tin để trả lời.
Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng và dễ hiểu.

NGỮ CẢNH:
{context}

CÂU HỎI: {query}

TRẢ LỜI:"""

        return prompt

    def query_documents(self, query: str, collection_name: str):
        """Query documents and prepare a prompt for LLM.

        Args:
            query: User query string
            collection_name: Name of the collection to search

        Returns:
            Response including retrieved documents and LLM prompt
        """
        retrieved_docs = self.vector_store.query(query, collection_name)

        # Extract the actual document data
        docs = retrieved_docs

        # Create a prompt for LLM from the retrieved documents
        llm_prompt = self._create_prompt_from_docs(query, docs)

        # llm_prompt -> llm model -> response
       

        return {
            "code": 200,
            "success": True,
            "message": "Documents queried successfully",
            "data": {"docs": docs, "response": llm_prompt},
        }

    def delete_collection(self, collection_name: str):
        return {
            "code": 200,
            "success": True,
            "message": "Collection deleted successfully",
            "data": self.vector_store.delete(collection_name),
        }
