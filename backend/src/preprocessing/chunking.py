"""Semantic Chunking Strategies for RAG4GOV

This module implements various text chunking strategies for RAG applications:
1. Fixed-size chunking: Simple character-based chunking with fixed size
2. Recursive chunking: Hierarchical chunking based on separators
3. Semantic chunking: Embedding-based chunking that preserves meaning
4. Hybrid chunking: Combines multiple strategies for optimal results

Each chunker follows a common interface and can be used interchangeably.
"""

import re
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class BaseChunker:
    """Base class for all chunking strategies."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the chunker with size and overlap parameters.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents into chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Split a text string into chunks.
        
        Args:
            text: Text to split
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunked documents
        """
        if metadata is None:
            metadata = {}
        
        # Default implementation - subclasses should override for specific behavior
        chunks = self._get_chunks(text)
        return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
    
    def _get_chunks(self, text: str) -> List[str]:
        """Get chunks from text - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")