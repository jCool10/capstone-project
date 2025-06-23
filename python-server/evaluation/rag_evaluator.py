import json
import math
import sys
import os
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
import logging
from datetime import datetime
import re

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Add app directory to path to import services directly
app_dir = os.path.join(parent_dir, "app")
sys.path.append(app_dir)

# Import directly from services to avoid the __init__.py import issue
from services.rag_service import RAGService

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """RAG System Evaluator with standard IR metrics"""

    def __init__(self, ground_truth_file: str = "data/ground_truth.json"):
        """
        Initialize RAG Evaluator

        Args:
            ground_truth_file: Path to ground truth JSON file
        """
        self.ground_truth_file = ground_truth_file
        self.ground_truth = self.load_ground_truth()
        self.rag_service = RAGService()

        # Document ID mapping (chunk_id -> document_id)
        self.chunk_to_doc_mapping = {}

        logger.info(
            f"RAG Evaluator initialized with {len(self.ground_truth['test_cases'])} test cases"
        )

    def load_ground_truth(self) -> Dict[str, Any]:
        """Load ground truth from JSON file"""
        try:
            with open(self.ground_truth_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ground truth: {e}")
            return {"test_cases": []}

    def create_chunk_to_doc_mapping(self, collection_name: str):
        """
        Create mapping from chunk IDs to document IDs
        This is crucial since documents are split into chunks
        """
        logger.info("Creating chunk to document mapping...")

        try:
            # Get collection stats to check if collection exists
            stats = self.rag_service.get_collection_stats(collection_name)
            if not stats.get("success", False):
                logger.warning(f"Collection {collection_name} not found")
                return

            # For now, we'll build mapping as chunks are encountered during evaluation
            # This is more efficient than scanning the entire collection upfront
            logger.info(
                "Chunk to document mapping will be built dynamically during evaluation"
            )

            # Initialize empty mapping - will be populated during evaluation
            self.chunk_to_doc_mapping = {}

        except Exception as e:
            logger.error(f"Error creating chunk mapping: {e}")
            # Fallback: use empty mapping and rely on text-based detection
            self.chunk_to_doc_mapping = {}

    def update_chunk_mapping(self, chunk_id: str, doc_id: int):
        """
        Update the chunk to document mapping dynamically

        Args:
            chunk_id: The chunk ID
            doc_id: The document ID this chunk belongs to
        """
        if doc_id > 0:  # Only update for valid document IDs
            self.chunk_to_doc_mapping[chunk_id] = doc_id
            logger.debug(f"Updated mapping: {chunk_id} -> {doc_id}")

    def extract_document_id_from_chunk(self, chunk_result: Dict) -> int:
        """
        Extract document ID from a chunk result

        Args:
            chunk_result: Result from RAG system containing chunk info

        Returns:
            Document ID (1-10 for our test documents)
        """
        # Try different methods to extract document ID

        # Method 1: Check if chunk ID is in our mapping
        chunk_id = chunk_result.get("id", "")
        if chunk_id in self.chunk_to_doc_mapping:
            return self.chunk_to_doc_mapping[chunk_id]

        # Method 2: Parse from metadata
        metadata = chunk_result.get("metadata", {})
        if "document_id" in metadata:
            doc_id = metadata["document_id"]
            self.update_chunk_mapping(chunk_id, doc_id)
            return doc_id

        # Method 2.1: Check for file_name in metadata and extract doc number
        file_name = metadata.get("file_name", "")
        if "sample_documents" in file_name:
            # This is from our test file, try to parse from text
            pass

        # Method 3: Parse from text content - improved logic
        text = chunk_result.get("text", "").strip()

        # Method 3.1: Look for "Tài liệu X:" pattern anywhere in text
        doc_pattern = r"Tài liệu (\d+):"
        match = re.search(doc_pattern, text)
        if match:
            try:
                doc_num = int(match.group(1))
                if 1 <= doc_num <= 10:  # Validate range
                    self.update_chunk_mapping(chunk_id, doc_num)
                    return doc_num
            except (ValueError, AttributeError):
                pass

        # Method 3.2: Look for specific keywords that indicate document number
        doc_keywords = {
            1: [
                "Trí tuệ nhân tạo",
                "Machine Learning",
                "AI",
                "artificial intelligence",
                "deep learning",
                "neural",
                "supervised learning",
                "unsupervised learning",
                "reinforcement learning",
            ],
            2: [
                "Blockchain",
                "cryptocurrency",
                "Bitcoin",
                "Ethereum",
                "Satoshi Nakamoto",
                "smart contract",
                "DApps",
                "distributed ledger",
                "hash",
            ],
            3: [
                "Khoa học dữ liệu",
                "Data Science",
                "Python",
                "R",
                "Pandas",
                "NumPy",
                "Scikit-learn",
                "Matplotlib",
                "Big Data",
                "Hadoop",
                "Spark",
            ],
            4: [
                "Cybersecurity",
                "An ninh mạng",
                "phishing",
                "malware",
                "ransomware",
                "firewall",
                "encryption",
                "two-factor",
                "penetration testing",
            ],
            5: [
                "Cloud Computing",
                "DevOps",
                "AWS",
                "Azure",
                "Docker",
                "Kubernetes",
                "CI/CD",
                "containerization",
                "IaaS",
                "PaaS",
                "SaaS",
            ],
            6: [
                "Internet of Things",
                "IoT",
                "Smart Cities",
                "sensors",
                "Edge computing",
                "smart home",
                "Industrial IoT",
                "IIoT",
            ],
            7: [
                "Mobile Development",
                "App Design",
                "iOS",
                "Android",
                "React Native",
                "Flutter",
                "Xamarin",
                "UX",
                "UI",
                "PWA",
                "ASO",
            ],
            8: [
                "Web Development",
                "Frontend",
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Vue.js",
                "Angular",
                "Node.js",
                "SPA",
                "CDN",
            ],
            9: [
                "Database",
                "Data Management",
                "MySQL",
                "PostgreSQL",
                "NoSQL",
                "MongoDB",
                "Cassandra",
                "Redis",
                "SQL",
                "ETL",
            ],
            10: [
                "Software Engineering",
                "Agile",
                "SDLC",
                "Scrum",
                "TDD",
                "design patterns",
                "documentation",
                "maintainable",
            ],
        }

        # Count keyword matches for each document
        text_lower = text.lower()
        max_matches = 0
        best_doc_id = 0

        for doc_id, keywords in doc_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_doc_id = doc_id

        # Reduce threshold to 1 keyword for confident match (was 2)
        if max_matches >= 1:
            self.update_chunk_mapping(chunk_id, best_doc_id)
            return best_doc_id

        # Method 4: Use a simple heuristic based on position
        # This is a fallback and may not be accurate
        logger.warning(f"Could not extract document ID from chunk: {chunk_id}")
        logger.debug(f"Chunk text preview: {text[:200]}...")
        return 0  # Unknown document

    def calculate_precision_at_k(
        self, query_results: List[Dict], relevant_docs: List[int], k: int
    ) -> float:
        """
        Calculate Precision@k

        Args:
            query_results: List of retrieved documents
            relevant_docs: List of relevant document IDs
            k: Number of top results to consider

        Returns:
            Precision@k score
        """
        if k == 0 or not query_results:
            return 0.0

        top_k_results = query_results[:k]
        relevant_retrieved = 0

        for result in top_k_results:
            doc_id = self.extract_document_id_from_chunk(result)
            if doc_id in relevant_docs:
                relevant_retrieved += 1

        return relevant_retrieved / k

    def calculate_recall_at_k(
        self, query_results: List[Dict], relevant_docs: List[int], k: int
    ) -> float:
        """
        Calculate Recall@k

        Args:
            query_results: List of retrieved documents
            relevant_docs: List of relevant document IDs
            k: Number of top results to consider

        Returns:
            Recall@k score
        """
        if not relevant_docs or not query_results:
            return 0.0

        top_k_results = query_results[:k]
        relevant_retrieved = set()

        for result in top_k_results:
            doc_id = self.extract_document_id_from_chunk(result)
            if doc_id in relevant_docs:
                relevant_retrieved.add(doc_id)

        return len(relevant_retrieved) / len(relevant_docs)

    def calculate_mrr(
        self, query_results: List[Dict], relevant_docs: List[int]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank for a single query

        Args:
            query_results: List of retrieved documents
            relevant_docs: List of relevant document IDs

        Returns:
            Reciprocal rank score
        """
        if not query_results or not relevant_docs:
            return 0.0

        for rank, result in enumerate(query_results, 1):
            doc_id = self.extract_document_id_from_chunk(result)
            if doc_id in relevant_docs:
                return 1.0 / rank

        return 0.0

    def calculate_dcg_at_k(
        self, query_results: List[Dict], relevance_scores: Dict[int, int], k: int
    ) -> float:
        """
        Calculate Discounted Cumulative Gain@k

        Args:
            query_results: List of retrieved documents
            relevance_scores: Dict mapping document_id to relevance score
            k: Number of top results to consider

        Returns:
            DCG@k score
        """
        if k == 0 or not query_results:
            return 0.0

        dcg = 0.0
        top_k_results = query_results[:k]

        for i, result in enumerate(top_k_results, 1):
            doc_id = self.extract_document_id_from_chunk(result)
            relevance = relevance_scores.get(doc_id, 0)

            if i == 1:
                dcg += relevance
            else:
                dcg += relevance / math.log2(i)

        return dcg

    def calculate_ideal_dcg_at_k(
        self, relevance_scores: Dict[int, int], k: int
    ) -> float:
        """
        Calculate Ideal DCG@k (best possible ranking)

        Args:
            relevance_scores: Dict mapping document_id to relevance score
            k: Number of top results to consider

        Returns:
            IDCG@k score
        """
        if not relevance_scores:
            return 0.0

        # Sort relevance scores in descending order
        sorted_relevances = sorted(relevance_scores.values(), reverse=True)[:k]

        idcg = 0.0
        for i, relevance in enumerate(sorted_relevances, 1):
            if i == 1:
                idcg += relevance
            else:
                idcg += relevance / math.log2(i)

        return idcg

    def calculate_ndcg_at_k(
        self, query_results: List[Dict], relevance_scores: Dict[int, int], k: int
    ) -> float:
        """
        Calculate Normalized DCG@k

        Args:
            query_results: List of retrieved documents
            relevance_scores: Dict mapping document_id to relevance score
            k: Number of top results to consider

        Returns:
            nDCG@k score
        """
        dcg = self.calculate_dcg_at_k(query_results, relevance_scores, k)
        idcg = self.calculate_ideal_dcg_at_k(relevance_scores, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def create_relevance_scores(self, test_case: Dict) -> Dict[int, int]:
        """
        Create relevance scores for a test case

        Args:
            test_case: Single test case from ground truth

        Returns:
            Dict mapping document_id to relevance score
        """
        relevance_levels = self.ground_truth.get(
            "relevance_levels",
            {
                "highly_relevant": 3,
                "relevant": 2,
                "partially_relevant": 1,
                "not_relevant": 0,
            },
        )

        scores = {}

        # Highly relevant documents
        for doc_id in test_case.get("highly_relevant_docs", []):
            scores[doc_id] = relevance_levels["highly_relevant"]

        # Regular relevant documents
        for doc_id in test_case.get("relevant_docs", []):
            if doc_id not in scores:  # Don't overwrite highly relevant
                scores[doc_id] = relevance_levels["relevant"]

        return scores

    def evaluate_single_query(
        self, test_case: Dict, collection_name: str, search_method: str = "dense"
    ) -> Dict[str, Any]:
        """
        Evaluate a single query

        Args:
            test_case: Single test case from ground truth
            collection_name: Collection to search in
            search_method: "dense", "sparse", or "hybrid"

        Returns:
            Evaluation results for this query
        """
        query = test_case["query"]
        query_id = test_case["query_id"]
        relevant_docs = test_case["relevant_docs"]

        logger.info(f"Evaluating query {query_id}: {query} (method: {search_method})")

        # Get results from RAG system based on search method
        if search_method == "dense":
            # Dense only - vector search
            rag_result = self.rag_service.query_documents(
                query=query, collection_name=collection_name, use_hybrid=False
            )
        elif search_method == "sparse":
            # Sparse only - BM25 search
            rag_result = self._query_sparse_only(query, collection_name)
        elif search_method == "hybrid":
            # Hybrid - both vector and BM25
            rag_result = self.rag_service.query_documents(
                query=query, collection_name=collection_name, use_hybrid=True
            )
        else:
            logger.error(f"Unknown search method: {search_method}")
            return self._empty_result(query_id, query, search_method)

        if not rag_result.get("success", False):
            logger.error(f"RAG query failed for {query_id} with method {search_method}")
            return self._empty_result(query_id, query, search_method)

        query_results = rag_result["data"]["docs"]
        relevance_scores = self.create_relevance_scores(test_case)

        # Calculate metrics for different k values
        k_values = self.ground_truth.get("k_values", [1, 3, 5, 10])

        result = {
            "query_id": query_id,
            "query": query,
            "search_method": search_method,
            "total_results": len(query_results),
            "relevant_docs": relevant_docs,
            "precision_at_k": {},
            "recall_at_k": {},
            "ndcg_at_k": {},
            "mrr": self.calculate_mrr(query_results, relevant_docs),
        }

        # Calculate metrics for each k
        for k in k_values:
            result["precision_at_k"][f"@{k}"] = self.calculate_precision_at_k(
                query_results, relevant_docs, k
            )
            result["recall_at_k"][f"@{k}"] = self.calculate_recall_at_k(
                query_results, relevant_docs, k
            )
            result["ndcg_at_k"][f"@{k}"] = self.calculate_ndcg_at_k(
                query_results, relevance_scores, k
            )

        # Add search statistics if available
        search_stats = rag_result["data"].get("search_stats", {})
        result["search_stats"] = search_stats

        return result

    def _query_sparse_only(self, query: str, collection_name: str) -> Dict[str, Any]:
        """
        Query using only BM25 (sparse search)

        Args:
            query: Search query
            collection_name: Collection name

        Returns:
            RAG result format compatible with evaluation
        """
        logger.info(f"Attempting sparse search for: {query}")

        try:
            # Method 1: Use hybrid search engine's BM25 component
            logger.debug("Checking hybrid_engine availability...")
            if (
                hasattr(self.rag_service, "hybrid_engine")
                and self.rag_service.hybrid_engine
            ):
                logger.info("Hybrid engine found, attempting BM25 search...")

                try:
                    # IMPORTANT: Load BM25 index first before using _get_sparse_results
                    bm25_index = (
                        self.rag_service.hybrid_engine.get_or_create_bm25_index(
                            collection_name
                        )
                    )
                    if bm25_index and bm25_index.bm25:
                        logger.info(
                            f"BM25 index loaded successfully for {collection_name}"
                        )

                        bm25_results = (
                            self.rag_service.hybrid_engine._get_sparse_results(
                                query, collection_name, k=10
                            )
                        )

                        if bm25_results:
                            logger.info(
                                f"Hybrid engine BM25 returned {len(bm25_results)} results"
                            )
                            return {
                                "success": True,
                                "data": {
                                    "docs": bm25_results,
                                    "search_stats": {
                                        "method": "sparse_only",
                                        "total_results": len(bm25_results),
                                    },
                                },
                            }
                        else:
                            logger.warning("Hybrid engine BM25 returned empty results")
                    else:
                        logger.warning(
                            f"BM25 index not available or not built for {collection_name}"
                        )
                except Exception as e:
                    logger.error(f"Error with hybrid engine BM25: {e}")
            else:
                logger.warning("Hybrid engine not available")

            # Method 2: Try to use BM25 index directly
            logger.debug("Checking direct BM25 index access...")
            bm25_indices = getattr(self.rag_service, "bm25_indices", {})
            logger.debug(f"Available BM25 indices: {list(bm25_indices.keys())}")

            bm25_index = bm25_indices.get(collection_name)
            if bm25_index:
                logger.info(f"Direct BM25 index found for {collection_name}")
                try:
                    results = bm25_index.search(query, top_k=10)
                    logger.info(f"Direct BM25 search returned {len(results)} results")

                    return {
                        "success": True,
                        "data": {
                            "docs": results,
                            "search_stats": {
                                "method": "sparse_only_fallback",
                                "total_results": len(results),
                            },
                        },
                    }
                except Exception as e:
                    logger.error(f"Error with direct BM25 search: {e}")
            else:
                logger.warning(f"No BM25 index found for collection: {collection_name}")

            # Method 3: Try to access through hybrid_engine.bm25_indices
            logger.debug("Checking hybrid_engine.bm25_indices...")
            if (
                hasattr(self.rag_service, "hybrid_engine")
                and self.rag_service.hybrid_engine
            ):
                hybrid_bm25_indices = getattr(
                    self.rag_service.hybrid_engine, "bm25_indices", {}
                )
                logger.debug(
                    f"Hybrid engine BM25 indices: {list(hybrid_bm25_indices.keys())}"
                )

                hybrid_bm25_index = hybrid_bm25_indices.get(collection_name)
                if hybrid_bm25_index:
                    logger.info(f"Hybrid engine BM25 index found for {collection_name}")
                    try:
                        results = hybrid_bm25_index.search(query, top_k=10)
                        logger.info(
                            f"Hybrid engine BM25 index search returned {len(results)} results"
                        )

                        return {
                            "success": True,
                            "data": {
                                "docs": results,
                                "search_stats": {
                                    "method": "sparse_hybrid_engine",
                                    "total_results": len(results),
                                },
                            },
                        }
                    except Exception as e:
                        logger.error(f"Error with hybrid engine BM25 index: {e}")

            # No BM25 available
            logger.error(
                "BM25 index not available for sparse search through any method"
            )
            return {
                "success": False,
                "message": "BM25 index not available",
                "data": {"docs": []},
            }

        except Exception as e:
            logger.error(f"Error in sparse search: {e}")
            return {"success": False, "message": str(e), "data": {"docs": []}}

    def _empty_result(
        self, query_id: str, query: str, search_method: str
    ) -> Dict[str, Any]:
        """Create empty result for failed queries"""
        k_values = self.ground_truth.get("k_values", [1, 3, 5, 10])

        return {
            "query_id": query_id,
            "query": query,
            "search_method": search_method,
            "total_results": 0,
            "relevant_docs": [],
            "precision_at_k": {f"@{k}": 0.0 for k in k_values},
            "recall_at_k": {f"@{k}": 0.0 for k in k_values},
            "ndcg_at_k": {f"@{k}": 0.0 for k in k_values},
            "mrr": 0.0,
            "error": "Query failed",
        }

    def evaluate_all_queries(
        self, collection_name: str, search_method: str = "dense"
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all queries in ground truth

        Args:
            collection_name: Collection to search in
            search_method: "dense", "sparse", or "hybrid"

        Returns:
            List of evaluation results for all queries
        """
        test_cases = self.ground_truth.get("test_cases", [])
        results = []

        logger.info(f"Evaluating {len(test_cases)} queries with {search_method} search")

        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Progress: {i}/{len(test_cases)}")
            result = self.evaluate_single_query(
                test_case, collection_name, search_method
            )
            results.append(result)

        return results

    def calculate_average_metrics(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate average metrics across all queries

        Args:
            results: List of individual query results

        Returns:
            Averaged metrics
        """
        if not results:
            return {}

        k_values = self.ground_truth.get("k_values", [1, 3, 5, 10])

        # Initialize accumulators
        avg_precision = {f"@{k}": [] for k in k_values}
        avg_recall = {f"@{k}": [] for k in k_values}
        avg_ndcg = {f"@{k}": [] for k in k_values}
        mrr_scores = []

        # Collect scores
        for result in results:
            if "error" not in result:  # Skip failed queries
                for k in k_values:
                    key = f"@{k}"
                    avg_precision[key].append(result["precision_at_k"][key])
                    avg_recall[key].append(result["recall_at_k"][key])
                    avg_ndcg[key].append(result["ndcg_at_k"][key])

                mrr_scores.append(result["mrr"])

        # Calculate averages
        summary = {
            "total_queries": len(results),
            "successful_queries": len([r for r in results if "error" not in r]),
            "avg_precision_at_k": {},
            "avg_recall_at_k": {},
            "avg_ndcg_at_k": {},
            "mean_mrr": np.mean(mrr_scores) if mrr_scores else 0.0,
        }

        for k in k_values:
            key = f"@{k}"
            summary["avg_precision_at_k"][key] = (
                np.mean(avg_precision[key]) if avg_precision[key] else 0.0
            )
            summary["avg_recall_at_k"][key] = (
                np.mean(avg_recall[key]) if avg_recall[key] else 0.0
            )
            summary["avg_ndcg_at_k"][key] = (
                np.mean(avg_ndcg[key]) if avg_ndcg[key] else 0.0
            )

        return summary

    def compare_three_methods(
        self, dense_results: Dict, sparse_results: Dict, hybrid_results: Dict
    ) -> Dict[str, Any]:
        """
        Compare dense, sparse, and hybrid search results

        Args:
            dense_results: Results from dense search evaluation
            sparse_results: Results from sparse search evaluation
            hybrid_results: Results from hybrid search evaluation

        Returns:
            Comparison analysis of all three methods
        """
        dense_summary = dense_results.get("summary", {})
        sparse_summary = sparse_results.get("summary", {})
        hybrid_summary = hybrid_results.get("summary", {})

        if not all([dense_summary, sparse_summary, hybrid_summary]):
            return {"error": "Missing summary data for comparison"}

        k_values = self.ground_truth.get("k_values", [1, 3, 5, 10])

        comparison = {
            "evaluation_date": datetime.now().isoformat(),
            "methods_comparison": {},
            "improvement_analysis": {},
            "ranking": {},
        }

        # Compare each metric across all three methods
        for metric in ["avg_precision_at_k", "avg_recall_at_k", "avg_ndcg_at_k"]:
            comparison["methods_comparison"][metric] = {}
            comparison["improvement_analysis"][metric] = {}
            comparison["ranking"][metric] = {}

            for k in k_values:
                key = f"@{k}"
                dense_score = dense_summary.get(metric, {}).get(key, 0.0)
                sparse_score = sparse_summary.get(metric, {}).get(key, 0.0)
                hybrid_score = hybrid_summary.get(metric, {}).get(key, 0.0)

                comparison["methods_comparison"][metric][key] = {
                    "dense": dense_score,
                    "sparse": sparse_score,
                    "hybrid": hybrid_score,
                }

                # Calculate improvements relative to dense (baseline)
                if dense_score > 0:
                    sparse_improvement = (
                        (sparse_score - dense_score) / dense_score
                    ) * 100
                    hybrid_improvement = (
                        (hybrid_score - dense_score) / dense_score
                    ) * 100

                    comparison["improvement_analysis"][metric][key] = {
                        "sparse_vs_dense": f"{sparse_improvement:+.2f}%",
                        "hybrid_vs_dense": f"{hybrid_improvement:+.2f}%",
                        "hybrid_vs_sparse": (
                            f"{((hybrid_score - sparse_score) / sparse_score * 100):+.2f}%"
                            if sparse_score > 0
                            else "N/A"
                        ),
                    }
                else:
                    comparison["improvement_analysis"][metric][key] = {
                        "sparse_vs_dense": "N/A",
                        "hybrid_vs_dense": "N/A",
                        "hybrid_vs_sparse": "N/A",
                    }

                # Rank methods by performance
                scores = [
                    ("dense", dense_score),
                    ("sparse", sparse_score),
                    ("hybrid", hybrid_score),
                ]
                ranked = sorted(scores, key=lambda x: x[1], reverse=True)
                comparison["ranking"][metric][key] = [
                    method for method, score in ranked
                ]

        # Compare MRR
        dense_mrr = dense_summary.get("mean_mrr", 0.0)
        sparse_mrr = sparse_summary.get("mean_mrr", 0.0)
        hybrid_mrr = hybrid_summary.get("mean_mrr", 0.0)

        comparison["methods_comparison"]["mean_mrr"] = {
            "dense": dense_mrr,
            "sparse": sparse_mrr,
            "hybrid": hybrid_mrr,
        }

        if dense_mrr > 0:
            sparse_mrr_improvement = ((sparse_mrr - dense_mrr) / dense_mrr) * 100
            hybrid_mrr_improvement = ((hybrid_mrr - dense_mrr) / dense_mrr) * 100
            comparison["improvement_analysis"]["mean_mrr"] = {
                "sparse_vs_dense": f"{sparse_mrr_improvement:+.2f}%",
                "hybrid_vs_dense": f"{hybrid_mrr_improvement:+.2f}%",
                "hybrid_vs_sparse": (
                    f"{((hybrid_mrr - sparse_mrr) / sparse_mrr * 100):+.2f}%"
                    if sparse_mrr > 0
                    else "N/A"
                ),
            }
        else:
            comparison["improvement_analysis"]["mean_mrr"] = {
                "sparse_vs_dense": "N/A",
                "hybrid_vs_dense": "N/A",
                "hybrid_vs_sparse": "N/A",
            }

        # Rank MRR
        mrr_scores = [
            ("dense", dense_mrr),
            ("sparse", sparse_mrr),
            ("hybrid", hybrid_mrr),
        ]
        mrr_ranked = sorted(mrr_scores, key=lambda x: x[1], reverse=True)
        comparison["ranking"]["mean_mrr"] = [method for method, score in mrr_ranked]

        return comparison

    def run_full_evaluation(
        self, collection_name: str = "evaluation_collection"
    ) -> Dict[str, Any]:
        """
        Run complete evaluation comparing dense, sparse, and hybrid search

        Args:
            collection_name: Collection to evaluate against

        Returns:
            Complete evaluation results for all three methods
        """
        logger.info("Starting full RAG evaluation with three search methods...")

        # Create chunk to document mapping
        self.create_chunk_to_doc_mapping(collection_name)

        # Evaluate dense search
        logger.info("Evaluating dense search...")
        dense_query_results = self.evaluate_all_queries(collection_name, "dense")
        dense_summary = self.calculate_average_metrics(dense_query_results)

        # Evaluate sparse search
        logger.info("Evaluating sparse search...")
        sparse_query_results = self.evaluate_all_queries(collection_name, "sparse")
        sparse_summary = self.calculate_average_metrics(sparse_query_results)

        # Evaluate hybrid search
        logger.info("Evaluating hybrid search...")
        hybrid_query_results = self.evaluate_all_queries(collection_name, "hybrid")
        hybrid_summary = self.calculate_average_metrics(hybrid_query_results)

        # Create complete results
        results = {
            "evaluation_metadata": {
                "evaluation_date": datetime.now().isoformat(),
                "total_queries": len(self.ground_truth.get("test_cases", [])),
                "collection_name": collection_name,
                "ground_truth_file": self.ground_truth_file,
                "search_methods": ["dense", "sparse", "hybrid"],
            },
            "dense_search": {
                "query_results": dense_query_results,
                "summary": dense_summary,
            },
            "sparse_search": {
                "query_results": sparse_query_results,
                "summary": sparse_summary,
            },
            "hybrid_search": {
                "query_results": hybrid_query_results,
                "summary": hybrid_summary,
            },
        }

        # Add three-way comparison
        comparison = self.compare_three_methods(
            results["dense_search"], results["sparse_search"], results["hybrid_search"]
        )
        results["comparison"] = comparison

        logger.info("Full evaluation completed for all three search methods")
        return results

    def save_results(
        self, results: Dict[str, Any], output_file: str = "evaluation_results.json"
    ):
        """
        Save evaluation results to file

        Args:
            results: Evaluation results
            output_file: Output file path
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_summary(self, results: Dict[str, Any]):
        """
        Print a summary of evaluation results

        Args:
            results: Evaluation results
        """
        print("\n" + "=" * 80)
        print("RAG EVALUATION SUMMARY")
        print("=" * 80)

        metadata = results.get("evaluation_metadata", {})
        print(f"Evaluation Date: {metadata.get('evaluation_date', 'Unknown')}")
        print(f"Total Queries: {metadata.get('total_queries', 0)}")
        print(f"Collection: {metadata.get('collection_name', 'Unknown')}")

        # Dense search results
        dense_summary = results.get("dense_search", {}).get("summary", {})
        if dense_summary:
            print(f"\nDENSE SEARCH RESULTS:")
            print(
                f"  Precision@5: {dense_summary.get('avg_precision_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  Recall@5: {dense_summary.get('avg_recall_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  nDCG@5: {dense_summary.get('avg_ndcg_at_k', {}).get('@5', 0):.3f}"
            )
            print(f"  MRR: {dense_summary.get('mean_mrr', 0):.3f}")

        # Sparse search results
        sparse_summary = results.get("sparse_search", {}).get("summary", {})
        if sparse_summary:
            print(f"\nSPARSE SEARCH RESULTS:")
            print(
                f"  Precision@5: {sparse_summary.get('avg_precision_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  Recall@5: {sparse_summary.get('avg_recall_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  nDCG@5: {sparse_summary.get('avg_ndcg_at_k', {}).get('@5', 0):.3f}"
            )
            print(f"  MRR: {sparse_summary.get('mean_mrr', 0):.3f}")

        # Hybrid search results
        hybrid_summary = results.get("hybrid_search", {}).get("summary", {})
        if hybrid_summary:
            print(f"\nHYBRID SEARCH RESULTS:")
            print(
                f"  Precision@5: {hybrid_summary.get('avg_precision_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  Recall@5: {hybrid_summary.get('avg_recall_at_k', {}).get('@5', 0):.3f}"
            )
            print(
                f"  nDCG@5: {hybrid_summary.get('avg_ndcg_at_k', {}).get('@5', 0):.3f}"
            )
            print(f"  MRR: {hybrid_summary.get('mean_mrr', 0):.3f}")

        # Improvements
        comparison = results.get("comparison", {})
        improvements = comparison.get("improvement_analysis", {})
        rankings = comparison.get("ranking", {})

        if improvements and rankings:
            print(f"\nIMPROVEMENTS (vs Dense Baseline):")
            print(f"  Sparse Search:")
            print(
                f"    Precision@5: {improvements.get('avg_precision_at_k', {}).get('@5', {}).get('sparse_vs_dense', 'N/A')}"
            )
            print(
                f"    Recall@5: {improvements.get('avg_recall_at_k', {}).get('@5', {}).get('sparse_vs_dense', 'N/A')}"
            )
            print(
                f"    nDCG@5: {improvements.get('avg_ndcg_at_k', {}).get('@5', {}).get('sparse_vs_dense', 'N/A')}"
            )
            print(
                f"    MRR: {improvements.get('mean_mrr', {}).get('sparse_vs_dense', 'N/A')}"
            )

            print(f"  Hybrid Search:")
            print(
                f"    Precision@5: {improvements.get('avg_precision_at_k', {}).get('@5', {}).get('hybrid_vs_dense', 'N/A')}"
            )
            print(
                f"    Recall@5: {improvements.get('avg_recall_at_k', {}).get('@5', {}).get('hybrid_vs_dense', 'N/A')}"
            )
            print(
                f"    nDCG@5: {improvements.get('avg_ndcg_at_k', {}).get('@5', {}).get('hybrid_vs_dense', 'N/A')}"
            )
            print(
                f"    MRR: {improvements.get('mean_mrr', {}).get('hybrid_vs_dense', 'N/A')}"
            )

            print(f"\nRANKINGS (Best to Worst):")
            print(
                f"  Precision@5: {' > '.join(rankings.get('avg_precision_at_k', {}).get('@5', []))}"
            )
            print(
                f"  Recall@5: {' > '.join(rankings.get('avg_recall_at_k', {}).get('@5', []))}"
            )
            print(
                f"  nDCG@5: {' > '.join(rankings.get('avg_ndcg_at_k', {}).get('@5', []))}"
            )
            print(f"  MRR: {' > '.join(rankings.get('mean_mrr', []))}")

        print("=" * 80)

    def debug_chunk_structure(self, chunk_result: Dict) -> None:
        """
        Debug method to analyze chunk structure

        Args:
            chunk_result: Result from RAG system containing chunk info
        """
        print("\n" + "=" * 50)
        print("CHUNK STRUCTURE DEBUG")
        print("=" * 50)

        print(f"Keys in chunk_result: {list(chunk_result.keys())}")
        print(f"Chunk ID: {chunk_result.get('id', 'NOT_FOUND')}")
        print(f"Chunk ID type: {type(chunk_result.get('id', ''))}")

        metadata = chunk_result.get("metadata", {})
        print(f"Metadata keys: {list(metadata.keys())}")
        print(f"Metadata content: {metadata}")

        text = chunk_result.get("text", "")
        print(f"Text length: {len(text)}")
        print(f"Text preview (first 300 chars): {text[:300]}...")

        # Check for document patterns
        doc_pattern = r"Tài liệu (\d+):"
        match = re.search(doc_pattern, text)
        print(f"Document pattern match: {match.group(1) if match else 'NOT_FOUND'}")

        print("=" * 50)

    def debug_sparse_search_availability(self, collection_name: str) -> Dict[str, Any]:
        """
        Debug method to check sparse search availability

        Args:
            collection_name: Collection to check

        Returns:
            Debug information about BM25 availability
        """
        debug_info = {
            "collection_name": collection_name,
            "hybrid_engine_available": False,
            "direct_bm25_available": False,
            "hybrid_bm25_available": False,
            "available_indices": [],
            "error_messages": [],
            "test_search_successful": False,
        }

        try:
            # Check hybrid engine
            if (
                hasattr(self.rag_service, "hybrid_engine")
                and self.rag_service.hybrid_engine
            ):
                debug_info["hybrid_engine_available"] = True
                logger.info("Hybrid engine found")

                # Check hybrid engine BM25 indices
                hybrid_bm25_indices = getattr(
                    self.rag_service.hybrid_engine, "bm25_indices", {}
                )
                debug_info["available_indices"].extend(
                    [f"hybrid:{k}" for k in hybrid_bm25_indices.keys()]
                )

                if collection_name in hybrid_bm25_indices:
                    debug_info["hybrid_bm25_available"] = True
                    logger.info(f"Hybrid BM25 index found for {collection_name}")

                    # Test search with hybrid engine
                    try:
                        test_results = (
                            self.rag_service.hybrid_engine._get_sparse_results(
                                "machine learning", collection_name, k=3
                            )
                        )
                        if test_results:
                            debug_info["test_search_successful"] = True
                            debug_info["test_results_count"] = len(test_results)
                            logger.info(
                                f"Hybrid BM25 test search successful: {len(test_results)} results"
                            )
                        else:
                            logger.warning(
                                "Hybrid BM25 test search returned empty results"
                            )
                    except Exception as e:
                        debug_info["error_messages"].append(
                            f"Hybrid BM25 test failed: {e}"
                        )
                        logger.error(f"Hybrid BM25 test search failed: {e}")
            else:
                logger.warning("Hybrid engine not available")

            # Check direct BM25 indices
            bm25_indices = getattr(self.rag_service, "bm25_indices", {})
            debug_info["available_indices"].extend(
                [f"direct:{k}" for k in bm25_indices.keys()]
            )

            if collection_name in bm25_indices:
                debug_info["direct_bm25_available"] = True
                logger.info(f"Direct BM25 index found for {collection_name}")

                # Test direct BM25 search
                try:
                    bm25_index = bm25_indices[collection_name]
                    test_results = bm25_index.search("machine learning", top_k=3)
                    if test_results:
                        debug_info["test_search_successful"] = True
                        debug_info["test_results_count"] = len(test_results)
                        logger.info(
                            f"Direct BM25 test search successful: {len(test_results)} results"
                        )
                    else:
                        logger.warning("Direct BM25 test search returned empty results")
                except Exception as e:
                    debug_info["error_messages"].append(f"Direct BM25 test failed: {e}")
                    logger.error(f"Direct BM25 test search failed: {e}")

        except Exception as e:
            debug_info["error_messages"].append(str(e))
            logger.error(f"Error in debug sparse search: {e}")

        return debug_info

    def test_sparse_search_simple(self, collection_name: str) -> bool:
        """
        Simple test for sparse search functionality

        Args:
            collection_name: Collection to test

        Returns:
            True if sparse search works, False otherwise
        """
        logger.info(f"Testing sparse search for collection: {collection_name}")

        try:
            # Try the _query_sparse_only method with a simple query
            result = self._query_sparse_only("machine learning", collection_name)

            if result.get("success", False):
                docs = result.get("data", {}).get("docs", [])
                logger.info(f"Sparse search test successful: {len(docs)} results")
                return len(docs) > 0
            else:
                logger.warning(
                    f"Sparse search test failed: {result.get('message', 'Unknown error')}"
                )
                return False

        except Exception as e:
            logger.error(f"Error in sparse search test: {e}")
            return False

    def run_complete_evaluation_pipeline(
        self,
        collection_name: str = "evaluation_collection",
        data_file_path: str = "data/sample_documents.txt",
    ) -> Dict[str, Any]:
        """
        Run complete evaluation pipeline: embed data -> evaluate all search methods

        Args:
            collection_name: Collection name to use
            data_file_path: Path to the data file to embed

        Returns:
            Complete evaluation results
        """
        logger.info("Starting complete RAG evaluation pipeline...")

        # Step 1: Check if collection exists and has data
        stats = self.rag_service.get_collection_stats(collection_name)
        collection_exists = stats.get("success", False)

        if collection_exists:
            entity_count = stats.get("data", {}).get("entity_count", 0)
            logger.info(
                f"Collection '{collection_name}' exists with {entity_count} entities"
            )

            if entity_count == 0:
                logger.info("Collection is empty, will embed data...")
                collection_exists = False
        else:
            logger.info(
                f"Collection '{collection_name}' does not exist, will create and embed data..."
            )

        # Step 2: Embed data if collection doesn't exist or is empty
        if not collection_exists:
            logger.info("Embedding documents into collection...")

            # Check if data file exists
            if not os.path.exists(data_file_path):
                raise FileNotFoundError(f"Data file not found: {data_file_path}")

            # Embed the document
            embed_result = self.rag_service.embed_documents(
                [data_file_path], collection_name
            )

            if not embed_result.get("success", False):
                raise Exception(
                    f"Failed to embed documents: {embed_result.get('message', 'Unknown error')}"
                )

            logger.info("Documents embedded successfully!")

            # Verify embedding
            stats = self.rag_service.get_collection_stats(collection_name)
            if stats.get("success", False):
                entity_count = stats.get("data", {}).get("entity_count", 0)
                logger.info(f"Collection now has {entity_count} entities")
            else:
                logger.warning("Could not verify collection stats after embedding")

        # Step 3: Run full evaluation
        logger.info("Starting evaluation of all search methods...")
        results = self.run_full_evaluation(collection_name)

        # Step 4: Save results
        output_file = f"evaluation_results_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_results(results, output_file)

        # Step 5: Print summary
        self.print_summary(results)

        logger.info("Complete evaluation pipeline finished!")
        return results


def main():
    """Main function to run the complete evaluation pipeline"""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG System Complete Evaluation Pipeline"
    )
    parser.add_argument(
        "--collection", default="evaluation_collection", help="Collection name to use"
    )
    parser.add_argument(
        "--data", default="data/sample_documents.txt", help="Path to data file to embed"
    )
    parser.add_argument(
        "--ground-truth",
        default="data/ground_truth.json",
        help="Path to ground truth file",
    )
    parser.add_argument(
        "--force-reembed",
        action="store_true",
        help="Force re-embedding even if collection exists",
    )

    args = parser.parse_args()

    try:
        # Initialize evaluator
        evaluator = RAGEvaluator(ground_truth_file=args.ground_truth)

        # If force re-embed, delete existing collection first
        if args.force_reembed:
            logger.info(
                f"Force re-embed enabled, deleting collection '{args.collection}' if it exists..."
            )
            delete_result = evaluator.rag_service.delete_collection(args.collection)
            if delete_result.get("success", False):
                logger.info("Collection deleted successfully")
            else:
                logger.info("Collection deletion skipped (may not exist)")

        # Run complete pipeline
        results = evaluator.run_complete_evaluation_pipeline(
            collection_name=args.collection, data_file_path=args.data
        )

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Results saved to: evaluation_results_{args.collection}_*.json")
        print("Check the summary above for detailed metrics.")

    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}")
        print(f"\nERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
