"""Fixed-Size Chunking Strategy for RAG4GOV.

This module implements a simple fixed-size chunking strategy that splits text
into chunks of approximately equal size.
"""

import logging
from typing import List, Dict, Optional, Any
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from ..chunking import BaseChunker

logger = logging.getLogger(__name__)

class FixedSizeChunker(BaseChunker):
    """Fixed-size chunker that splits text into chunks of approximately equal size."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the fixed-size chunker.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        super().__init__(chunk_size, chunk_overlap)
        self.splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=" "  # Split on spaces to avoid cutting words
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents into chunks of fixed size.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        return self.splitter.split_documents(documents)
    
    def _get_chunks(self, text: str) -> List[str]:
        """Get chunks from text using fixed-size splitting.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Split a text string into chunks of fixed size.
        
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