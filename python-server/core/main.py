"""
Example application demonstrating the use of LangChain-Lite with all components
"""

import os
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# set the working directory to the directory of the file

# Import components from LangChain-Lite
from core.chains.rag import RagChain
from core.document_loaders.directory import DirectoryLoader
from core.text_splitters.sentence import SentenceSplitter
from core.embeddings.huggingface import HuggingFaceEmbedding
from core.vector_stores.in_memory import InMemoryVectorStore
from core.retrievers.base import VectorStoreRetriever
from core.llms.huggingface import HuggingFaceLLM

# Default directories
DEFAULT_DATA_DIR = "data"
DEFAULT_MODEL_DIR = "models"
DEFAULT_CACHE_DIR = ".cache"

def setup_rag_system(
    data_dir: str,
    model_dir: str,
    cache_dir: str,
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    llm_model_name: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    verbose: bool = False
):
    """Set up a complete RAG system."""
    os.makedirs(cache_dir, exist_ok=True)
    
    # Step 1: Set up document loader
    loader = DirectoryLoader(
        path=data_dir, 
        glob_pattern="**/*.*",
        recursive=True,
        exclude_hidden=True,
        show_progress=verbose
    )
    
    if verbose:
        print(f"Loading documents from {data_dir}...")
    start_time = time.time()
    documents = loader.load()
    if verbose:
        print(f"Loaded {len(documents)} documents in {time.time() - start_time:.2f}s")
    
    # Step 2: Set up text splitter
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    if verbose:
        print("Splitting documents into chunks...")
    start_time = time.time()
    chunks = splitter.split_documents(documents)
    if verbose:
        print(f"Created {len(chunks)} chunks in {time.time() - start_time:.2f}s")
    
    # Step 3: Set up embedding model
    embeddings = HuggingFaceEmbedding(
        model_name=embedding_model_name,
        normalize=True,
        cache_folder=cache_dir
    )
    
    # Step 4: Set up vector store and add documents
    vector_store = InMemoryVectorStore(embedding_model=embeddings)
    
    if verbose:
        print("Adding documents to vector store...")
    start_time = time.time()
    vector_store.add_documents(chunks)
    if verbose:
        print(f"Added documents to vector store in {time.time() - start_time:.2f}s")
    
    # Step 5: Set up retriever
    retriever = VectorStoreRetriever(
        vector_store=vector_store,
        search_kwargs={"k": 4}
    )
    
    # Step 6: Set up LLM if model_dir provided
    if llm_model_name:
        if verbose:
            print(f"Loading LLM model {llm_model_name}...")
        llm = HuggingFaceLLM(
            model_name=llm_model_name,
            cache_folder=cache_dir
        )
        
        # Step 7: Set up RAG chain
        rag_chain = RagChain(
            retriever=retriever,
            llm=llm,
            return_source_documents=True,
            verbose=verbose
        )
        
        return rag_chain
    else:
        return retriever


def interactive_mode(rag_system: Any, is_chain: bool = True):
    """Run in interactive mode."""
    print("\n" + "=" * 60)
    print("LangChain-Lite RAG System".center(60))
    print("=" * 60)
    print("Type 'exit' to quit or 'help' for commands")
    
    while True:
        query = input("\nEnter your query: ")
        
        if query.lower() == "exit":
            print("Exiting...")
            break
        elif query.lower() == "help":
            print("\nAvailable commands:")
            print("  exit - Exit the program")
            print("  help - Show this help message")
            continue
        
        start_time = time.time()
        
        if is_chain:
            # We have a full RAG chain with LLM
            result = rag_system(query)
            
            print("\n" + "=" * 60)
            print("ANSWER:")
            print(result["answer"])
            print("-" * 60)
            print(f"Time: {time.time() - start_time:.2f}s")
            
            show_sources = input("\nShow sources? (y/n): ").lower() == "y"
            if show_sources and "source_documents" in result:
                print("\nSOURCES:")
                for i, doc in enumerate(result["source_documents"]):
                    print(f"\n[{i+1}] {doc.metadata.get('file_name', 'Unknown source')}")
                    print(f"    {doc.page_content[:200]}...")
        else:
            # We only have a retriever
            docs = rag_system.get_relevant_documents(query)
            
            print("\n" + "=" * 60)
            print(f"Found {len(docs)} relevant documents:")
            print("-" * 60)
            
            for i, doc in enumerate(docs):
                print(f"\n[{i+1}] {doc.metadata.get('file_name', 'Unknown source')}")
                print(f"    {doc.page_content[:300]}...")
            
            print(f"\nTime: {time.time() - start_time:.2f}s")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LangChain-Lite RAG Example")
    parser.add_argument("--data", default=DEFAULT_DATA_DIR, help="Directory containing documents")
    parser.add_argument("--model", default=None, help="Directory containing LLM model")
    parser.add_argument("--cache", default=DEFAULT_CACHE_DIR, help="Cache directory")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2", 
                       help="Embedding model name")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size for document splitting")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap for document splitting")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        print(f"Data directory {args.data} does not exist!")
        return
        
    # Set up the RAG system
    rag_system = setup_rag_system(
        data_dir=args.data,
        model_dir=args.model,
        cache_dir=args.cache,
        embedding_model_name=args.embedding_model,
        llm_model_name=args.model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        verbose=args.verbose
    )
    
    # Determine if we have a chain or just a retriever
    is_chain = hasattr(rag_system, "llm")
    
    # Start interactive mode
    interactive_mode(rag_system, is_chain)


if __name__ == "__main__":
    main() 