"""
Reranker model implementation for the RAG system.

This module provides the RerankerModel class which handles:
- Initialization of Cross-Encoder models
- Reranking retrieved documents based on query relevance
"""
import logging
from typing import List, Tuple, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class RerankerModel:
    """
    Manages reranking of retrieved documents using a Cross-Encoder.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L12-v2"):
        """
        Initialize the reranker model.
        
        Args:
            model_name: Name of the Cross-Encoder model to use
        """
        logger.info(f"Initializing Reranker model: {model_name}")
        try:
            # Using CPU for stability as per requirements
            self.model = CrossEncoder(model_name, device="cpu")
            logger.info("Reranker model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Reranker model: {e}")
            raise e

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Rerank a list of retrieved documents.
        
        Args:
            query: The user query
            documents: List of document dicts (must contain 'text' or 'content')
            top_k: Number of top results to return after reranking
            
        Returns:
            Sorted list of documents based on cross-encoder scores
        """
        if not documents:
            return []
            
        # Prepare pairs for cross-encoder: (query, doc_text)
        # We try to find text in 'text', 'content', or 'page_content'
        pairs = []
        for doc in documents:
            text = doc.get("text") or doc.get("content") or doc.get("page_content", "")
            pairs.append((query, text))
            
        # Predict relevance scores
        try:
            scores = self.model.predict(pairs)
            
            # Attach scores to documents and sort
            for i, score in enumerate(scores):
                documents[i]["rerank_score"] = float(score)
                
            # Sort by score descending
            reranked_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
            
            return reranked_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # On failure, return original documents as fallback
            return documents[:top_k]
