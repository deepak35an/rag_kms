"""
BM25 Retriever for ViDoRe Evaluation

Provides sparse keyword-based retrieval using BM25 algorithm.
"""
import logging
import asyncio
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import numpy as np

logger = logging.getLogger(__name__)

class BM25Retriever:
    """
    BM25-based sparse retriever for keyword matching.
    """
    
    def __init__(self, corpus: List[Dict[str, str]]):
        """
        Initialize BM25 retriever with document corpus.
        
        Args:
            corpus: List of document dicts with 'id' and 'text' fields
        """
        self.corpus = corpus
        self.doc_ids = [doc['id'] for doc in corpus]
        
        # Tokenize corpus
        logger.info("Tokenizing corpus for BM25...")
        tokenized_corpus = [doc['text'].lower().split() for doc in corpus]
        
        # Initialize BM25
        logger.info("Building BM25 index...")
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 index built with {len(corpus)} documents")
        
    async def retrieve(self, query: str, k: int = 10) -> Tuple[List[str], List[float]]:
        """
        Retrieve top-K documents using BM25 scoring.
        
        Args:
            query: Query text
            k: Number of results to retrieve
            
        Returns:
            Tuple of (doc_ids, scores) in ranked order
        """
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = await asyncio.to_thread(
            self.bm25.get_scores, 
            tokenized_query
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(scores)[::-1][:k]
        
        # Extract doc IDs and scores
        top_doc_ids = [self.doc_ids[i] for i in top_k_indices]
        top_scores = [float(scores[i]) for i in top_k_indices]
        
        return top_doc_ids, top_scores
