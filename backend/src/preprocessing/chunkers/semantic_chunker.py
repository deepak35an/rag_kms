"""Semantic Chunking Strategy for RAG4GOV.

This module implements a semantic chunking strategy that uses embeddings to create
chunks that are semantically coherent.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any, Callable
from langchain_core.documents import Document
from ..chunking import BaseChunker
import re

logger = logging.getLogger(__name__)

class SemanticChunker(BaseChunker):
    """Semantic chunker that creates semantically coherent chunks using embeddings."""
    
    def __init__(self, embedding_function: Callable, chunk_size: int = 1000, 
                 chunk_overlap: int = 200, similarity_threshold: float = 0.75):
        """Initialize the semantic chunker.
        
        Args:
            embedding_function: Function to generate embeddings for text
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            similarity_threshold: Threshold for semantic similarity to merge chunks
        """
        super().__init__(chunk_size, chunk_overlap)
        self.embedding_function = embedding_function
        self.similarity_threshold = similarity_threshold
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents into semantically coherent chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        result = []
        for doc in documents:
            chunks = self.split_text(doc.page_content, doc.metadata)
            result.extend(chunks)
        return result
    
    def _get_chunks(self, text: str) -> List[str]:
        """Get semantically coherent chunks from text using adaptive breakpoints."""
        # 1. Split into sentences (simple regex-based sentence splitter)
        # We split by periods, exclamation marks, or question marks followed by space/newline
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if not sentences:
            return []
        if len(sentences) == 1:
            return sentences

        # 2. Convert sentences to "windows" for better semantic context
        # We combine each sentence with its immediate neighbors (buffer size 1)
        # This reduces noise in single-sentence embeddings
        combined_sentences = []
        for i in range(len(sentences)):
            window = sentences[max(0, i-1):min(len(sentences), i+2)]
            combined_sentences.append(" ".join(window))

        # 3. Get embeddings for the combined windows
        try:
            embeddings = [self.embedding_function.embed_query(s) for s in combined_sentences]
        except Exception as e:
            logger.error(f"Error generating embeddings for semantic chunking: {e}")
            return [text] # Fallback to no splitting on error

        # 4. Calculate distances between adjacent sentences
        distances = []
        for i in range(len(embeddings) - 1):
            similarity = self._cosine_similarity(embeddings[i], embeddings[i+1])
            distances.append(1 - similarity) # Distance is 1 - CosSim

        if not distances:
            return [text]

        # 5. Identify adaptive breakpoints
        # Instead of a fixed threshold, we look for distances that are "large" 
        # relative to the rest of the document (e.g., above 90th percentile)
        breakpoint_percentile_threshold = 92 # Configurable
        breakpoint_distance_threshold = np.percentile(distances, breakpoint_percentile_threshold)
        
        # We also enforce a minimum distance to avoid over-splitting 
        # (if the whole document is very similar)
        min_distance = 0.1
        final_threshold = max(breakpoint_distance_threshold, min_distance)

        # 6. Group sentences into chunks based on breakpoints
        chunks = []
        current_chunk_sentences = [sentences[0]]
        
        for i, distance in enumerate(distances):
            sentence = sentences[i+1]
            
            # Check if this is a breakpoint
            is_breakpoint = distance > final_threshold
            
            # Estimate current chunk length if we add this sentence
            current_length = sum(len(s) for s in current_chunk_sentences) + len(sentence)
            
            if is_breakpoint or current_length > self.chunk_size:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = [sentence]
            else:
                current_chunk_sentences.append(sentence)
        
        # Add final chunk
        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
        return chunks
    
    def _cosine_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings."""
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)
        
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
    
    def _average_embeddings(self, embeddings, weights=None):
        """Calculate weighted average of embeddings."""
        if weights is None:
            weights = [1] * len(embeddings)
        
        # Convert to numpy arrays
        embeddings = [np.array(emb) for emb in embeddings]
        weights = np.array(weights) / sum(weights)  # Normalize weights
        
        # Calculate weighted average
        avg_embedding = sum(w * emb for w, emb in zip(weights, embeddings))
        
        # Normalize to unit length
        return avg_embedding / np.linalg.norm(avg_embedding)
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Split a text string into semantically coherent chunks.
        
        Args:
            text: Text to split
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunked documents
        """
        if metadata is None:
            metadata = {}
        
        chunks = self._get_chunks(text)
        return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]