from typing import Any, Dict, List, Optional, Union
import time

from .base import Chain
from ..document import Document
from ..retrievers.base import BaseRetriever
from ..retrievers.reranker import Reranker
from ..llms.base import BaseLLM

class RagChain(Chain):
    """Retrieval-Augmented Generation chain."""
    
    def __init__(
        self,
        retriever: BaseRetriever,
        llm: BaseLLM,
        return_source_documents: bool = False,
        verbose: bool = False,
        rerank_top_k: int = 3,
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        """Initialize with retriever and LLM."""
        self.retriever = retriever
        self.llm = llm
        self.return_source_documents = return_source_documents
        self.verbose = verbose
        
        # Initialize reranker
        self.reranker = Reranker(
            model_name=rerank_model,
            device="auto",
            top_k=rerank_top_k
        )
        
    def _create_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Create a prompt from the query and retrieved documents."""
        # Format documents
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above. Do not repeat the question or include the prompt template in your response.

Answer:"""
        
        return prompt
        
    def run(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Run the chain on the input data."""
        if self.verbose:
            print(f"Retrieving documents for query: {input_data}")
            
        # Retrieve relevant documents
        start_time = time.time()
        documents = self.retriever.get_relevant_documents(input_data)
        if self.verbose:
            print(f"Retrieved {len(documents)} documents in {time.time() - start_time:.2f}s")
            
        # Rerank documents
        if self.verbose:
            print("Reranking documents...")
        start_time = time.time()
        reranked_docs = self.reranker.rerank(input_data, documents)
        if self.verbose:
            print(f"Reranked documents in {time.time() - start_time:.2f}s")
            print(f"Selected top {len(reranked_docs)} most relevant documents")
            
        # Create prompt
        prompt = self._create_prompt(input_data, reranked_docs)
        
        # Generate answer
        if self.verbose:
            print("Generating answer")
        start_time = time.time()
        answer = self.llm.generate(prompt, **kwargs)
        
        # Clean up answer
        answer = answer.strip()
        if answer.startswith("Answer:"):
            answer = answer[7:].strip()
            
        if self.verbose:
            print(f"Generated answer in {time.time() - start_time:.2f}s")
            
        # Prepare result
        result = {"answer": answer}
        
        if self.return_source_documents:
            result["source_documents"] = reranked_docs
            
        return result 