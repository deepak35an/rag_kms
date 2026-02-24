"""Recursive Chunking Strategy for RAG4GOV.

This module implements a recursive chunking strategy that splits text hierarchically
based on separators like paragraphs, sentences, etc.
"""

import logging
from typing import List, Dict, Optional, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..chunking import BaseChunker

logger = logging.getLogger(__name__)

class RecursiveChunker(BaseChunker):
    """Recursive chunker that splits text hierarchically based on separators."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 separators: Optional[List[str]] = None):
        """Initialize the recursive chunker.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            separators: List of separators to use for splitting, in order of priority
        """
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",    # Line breaks
            ".",     # Sentences
            ";",     # Semicolons
            ":",     # Colons
            " ",     # Words
            "",      # Characters
        ]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            keep_separator=True
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents into chunks using recursive splitting.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        return self.splitter.split_documents(documents)
    
    def _get_chunks(self, text: str) -> List[str]:
        """Get chunks from text using recursive splitting.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Split a text string into chunks using recursive splitting.
        
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