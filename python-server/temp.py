from pymilvus import connections, Collection, DataType, FieldSchema, CollectionSchema, utility
from pymilvus import MilvusClient, model
import logging
import json
import concurrent.futures
from typing import List, Dict, Any
import math
import time
from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusVectorStore:
    """Milvus vector store implementation."""

    def __init__(
        self, 
        uri:str,
        embedding_name:str,
        metric_type:str = "COSINE",
        num_threads:int = 4,
        batch_size:int = 8,
        reranker_name:str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.uri = uri
        self.client = self._connect_milvus(uri)
        self.embedding_model = self._create_embedding_model(embedding_name)
        self.reranker = CrossEncoder(reranker_name)
        self.embed_dim = None
        self.metric_type = metric_type
        self.num_threads = num_threads
        self.batch_size = batch_size
        logger.info(f"Initialized MilvusVectorStore successfully")

    def _connect_milvus(self, uri:str):
        try:
            client = MilvusClient(uri)
            logger.info(f"Successfully connected to Milvus at {uri}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Milvus at {uri}: {e}")
            raise
      
    def _create_embedding_model(self, embedding_name:str):
        """Create the embedding model if not already initialized."""
        if embedding_name == "bge-m3":
            return model.hybrid.BGEM3EmbeddingFunction(
                model_name='BAAI/bge-m3',
                device='cpu',
                use_fp16=False
            )
        else:
            raise ValueError(f"Embedding {embedding_name} not supported")

    def _embed_batch(self, doc_batch: List) -> List[Dict]:
        """Embed a batch of documents in parallel.
        
        Args:
            doc_batch: List of Document objects to embed
            
        Returns:
            List of dictionaries containing document data with embeddings
        """
        if not doc_batch:
            return []
            
        # Ensure embedding model is initialized
        if self.embedding_model is None:
            self._create_embedding_model(self.embedding_name)
            
        # Extract document contents for batch embedding
        contents = [doc.page_content for doc in doc_batch]
        
        # Batch embed the documents (faster than one by one)
        try:
            start_time = time.time()
            embedding_results = self.embedding_model.encode_documents(contents)
            vectors = embedding_results['dense']
            embedding_time = time.time() - start_time
            logger.info(f"Embedded batch of {len(doc_batch)} docs in {embedding_time:.2f}s ({len(doc_batch)/embedding_time:.2f} docs/sec)")
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            raise
            
        # Combine document data with embeddings
        processed_docs = []
        for i, doc in enumerate(doc_batch):
            vector = vectors[i].tolist()
            
            # Use the first batch to determine embedding dimension
            if self.embed_dim is None and i == 0:
                self.embed_dim = len(vector)
                logger.info(f"Detected embedding dimension: {self.embed_dim}")
                
            # Convert document metadata to JSON string if it exists
            metadata_str = json.dumps(doc.metadata) if hasattr(doc, 'metadata') and doc.metadata else "{}"
            
            # Create data entry for Milvus
            data_entry = {
                "id": doc.id_,
                "vector": vector,
                "text": doc.page_content,
                "metadata": metadata_str
            }
            processed_docs.append(data_entry)
            
        return processed_docs
        
    def add(self, documents, collection_name):
        """Add documents to Milvus collection using multi-threaded batch processing."""
        try:
            total_docs = len(documents)
            if not total_docs:
                logger.warning("No documents to add")
                return False
                
            # Ensure embedding model is initialized
            if self.embedding_model is None:
                try:
                    self._create_embedding_model(self.embedding_name)
                except Exception as e:
                    logger.error(f"Failed to initialize embedding model: {e}")
                    return False
                
            # Split documents into batches
            num_batches = math.ceil(total_docs / self.batch_size)
            batches = []
            for i in range(num_batches):
                start_idx = i * self.batch_size
                end_idx = min((i + 1) * self.batch_size, total_docs)
                batches.append(documents[start_idx:end_idx])
                
            # Use ThreadPoolExecutor to process batches in parallel
            all_processed_docs = []
            embedding_errors = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                # Submit all batches for processing
                future_to_batch = {executor.submit(self._embed_batch, batch): i for i, batch in enumerate(batches)}
                
                # Collect results as they complete
                completed = 0
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        processed_batch = future.result()
                        all_processed_docs.extend(processed_batch)
                        completed += len(batches[batch_idx])
                        if batch_idx % 10 == 0 or batch_idx == num_batches - 1:  # Log less frequently
                            logger.info(f"Progress: {completed}/{total_docs} documents ({batch_idx+1}/{num_batches} batches)")
                    except Exception as e:
                        embedding_errors += 1
                        logger.error(f"Error processing batch {batch_idx}: {e}")
            
            # Ensure we got embeddings
            if not all_processed_docs:
                logger.error("No documents were successfully embedded")
                return False
                
            # Log warning if some batches failed
            if embedding_errors > 0:
                logger.warning(f"{embedding_errors}/{num_batches} batches failed during embedding")
        except Exception as e:
            logger.error(f"Unexpected error during document processing: {e}")
            return False
            
        # Check if collection exists and create if needed
        try:
            if not self.client.has_collection(collection_name):
                # Create collection with proper schema
                schema = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.embed_dim),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=32768)
                ]
                
                try:
                    self.client.create_collection(
                        collection_name=collection_name,
                        schema=schema,
                        index_params={
                            "vector": {"metric_type": self.metric_type, "index_type": "IVF_FLAT", "params": {"nlist": 128}}
                        }
                    )
                    logger.info(f"Successfully created collection {collection_name} with schema-based method")
                except Exception as e:
                    logger.warning(f"Falling back to legacy collection creation: {e}")
                    try:
                        self.client.create_collection(
                            collection_name, 
                            dimension=self.embed_dim,
                            id_type='string',
                            max_length=65_535,
                            metric_type=self.metric_type,
                        )
                        logger.info(f"Successfully created collection {collection_name} with legacy method")
                    except Exception as e2:
                        logger.error(f"Both collection creation methods failed for {collection_name}: {e2}")
                        return False
            else:
                try:
                    collection_info = self.client.describe_collection(collection_name)
                    if 'index_params' in str(collection_info):
                        logger.info(f"Collection {collection_name} already exists. Info: {collection_info}")
                except Exception as e:
                    logger.warning(f"Could not get collection info for {collection_name}: {e}")
        except Exception as e:
            logger.error(f"Error checking/creating collection {collection_name}: {e}")
            return False
        
        # Insert data with batch processing for large datasets
        max_insert_batch = 1000
        insert_batches = []
        for i in range(0, len(all_processed_docs), max_insert_batch):
            insert_batches.append(all_processed_docs[i:i + max_insert_batch])
        
        total_inserted = 0
        insertion_errors = 0
        
        for i, batch in enumerate(insert_batches):
            try:
                result = self.client.insert(collection_name, batch)
                total_inserted += len(batch)
                if i % 5 == 0 or i == len(insert_batches) - 1:
                    logger.info(f"Inserted batch {i+1}/{len(insert_batches)} ({total_inserted}/{len(all_processed_docs)} docs)")
            except Exception as e:
                insertion_errors += 1
                logger.error(f"Error inserting batch {i+1}: {e}")
                if i == 0 and len(batch) > 0:
                    logger.error(f"First doc schema: {list(batch[0].keys())}, vector len: {len(batch[0]['vector'])}")
        
        # Return True only if all documents were inserted successfully
        if total_inserted == len(all_processed_docs) and insertion_errors == 0:
            return True
        else:
            logger.error(f"Not all documents were inserted successfully. Inserted: {total_inserted}/{len(all_processed_docs)}, Errors: {insertion_errors}")
            return False

    def _bm25_search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        """Perform BM25 search on documents."""
        # Extract text content from documents
        texts = [doc['text'] for doc in documents]
        
        # Tokenize texts (simple whitespace tokenization for example)
        tokenized_texts = [text.split() for text in texts]
        tokenized_query = query.split()
        
        # Create BM25 model
        bm25 = BM25Okapi(tokenized_texts)
        
        # Get BM25 scores
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Create list of (score, index) tuples and sort by score
        scored_indices = [(score, idx) for idx, score in enumerate(bm25_scores)]
        scored_indices.sort(reverse=True)
        
        # Get top_k results
        results = []
        for score, idx in scored_indices[:top_k]:
            doc = documents[idx].copy()
            doc['bm25_score'] = float(score)
            results.append(doc)
            
        return results

    def _rerank_results(self, query: str, results: List[Dict], top_k: int = 3) -> List[Dict]:
        """Rerank results using cross-encoder."""
        if not results:
            return []
            
        # Prepare pairs for reranking
        pairs = [[query, result['text']] for result in results]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Add reranking scores to results
        for idx, score in enumerate(rerank_scores):
            results[idx]['rerank_score'] = float(score)
        
        # Sort by reranking score
        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return results[:top_k]

    def query(self, query, collection_name, limit=3, hybrid_search=True, rerank=True):
        """Query documents from Milvus collection using hybrid search (dense + sparse) and reranking."""
        if self.embedding_model is None:
            self._create_embedding_model(self.embedding_name)
        
        if not self.client.has_collection(collection_name):
            raise ValueError(f"Collection {collection_name} not found")
        
        start_time = time.time()
        
        # Dense vector search
        query_vector = self.embedding_model.encode_queries([query])['dense'][0].tolist()
        try:
            # Use larger limit for initial retrieval
            initial_limit = max(limit * 3, 10)
            search_params = {"metric_type": self.metric_type, "params": {}}
            
            # Search in Milvus collection
            search_start = time.time()
            search_results = self.client.search(
                collection_name=collection_name, 
                data=[query_vector],
                limit=initial_limit,
                search_params=search_params,
                output_fields=["text", "metadata"]
            )
            logger.info(f"Dense search completed in {time.time() - search_start:.2f}s")
            
            # Process initial results
            processed_results = []
            if search_results and len(search_results) > 0:
                for hit in search_results[0]:
                    metadata_str = hit.get('entity', {}).get('metadata', '{}')
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse metadata JSON")
                        metadata = {}
                    
                    metadata['vector_score'] = hit.get('distance')
                    
                    result = {
                        'id': hit.get('id'),
                        'text': hit.get('entity', {}).get('text', ''),
                        'metadata': metadata,
                        'vector_score': hit.get('distance')
                    }
                    processed_results.append(result)
            
            # Perform BM25 search if hybrid search is enabled
            if hybrid_search and processed_results:
                bm25_results = self._bm25_search(query, processed_results, top_k=initial_limit)
                
                # Combine scores (simple average for now)
                for doc in bm25_results:
                    doc['combined_score'] = (doc['vector_score'] + doc['bm25_score']) / 2
                
                # Sort by combined score
                bm25_results.sort(key=lambda x: x['combined_score'], reverse=True)
                processed_results = bm25_results
            
            # Rerank results if enabled
            if rerank and processed_results:
                processed_results = self._rerank_results(query, processed_results, top_k=limit)
            else:
                processed_results = processed_results[:limit]
            
            logger.info(f"Query returned {len(processed_results)} results in {time.time() - start_time:.2f}s")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise
    
    def update(self, collection_name, data):
        """Drop and recreate collection with new data."""
        if self.client.has_collection(collection_name):
            logger.info(f"Dropping collection {collection_name} for update")
            self.client.drop_collection(collection_name)
        
        return self.add(data, collection_name)
    
    def delete(self, collection_name):
        """Delete a collection."""
        if self.client.has_collection(collection_name):
            logger.info(f"Dropping collection {collection_name}")
            self.client.drop_collection(collection_name)
            return True
        return False
    
    def get_collection_stats(self, collection_name):
        """Get collection statistics."""
        return self.client.get_collection_stats(collection_name)
    
    def has_collection(self, collection_name):
        """Check if collection exists."""
        return self.client.has_collection(collection_name)
        
