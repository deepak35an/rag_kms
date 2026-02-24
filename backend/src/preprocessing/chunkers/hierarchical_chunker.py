"""Hierarchical Chunking Strategy for RAG4GOV.

This module implements a parent-child hierarchical chunking strategy.
"""

import logging
from typing import List, Dict, Optional, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..chunking import BaseChunker

logger = logging.getLogger(__name__)

class HierarchicalChunker(BaseChunker):
    """Hierarchical chunker that creates parent and child chunks."""
    
    def __init__(self, parent_size: int = 1500, parent_overlap: int = 200,
                 child_size: int = 400, child_overlap: int = 50,
                 separators: Optional[List[str]] = None):
        """Initialize the hierarchical chunker.
        
        Args:
            parent_size: Size of parent chunks
            parent_overlap: Overlap for parent chunks
            child_size: Size of child chunks
            child_overlap: Overlap for child chunks
            separators: Optional separators for recursive splitting
        """
        # We pass child_size to super for compatibility
        super().__init__(child_size, child_overlap)
        
        self.parent_size = parent_size
        self.parent_overlap = parent_overlap
        self.child_size = child_size
        self.child_overlap = child_overlap
        
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",    # Line breaks
            ". ",    # Sentences
            " ",     # Words
            "",      # Characters
        ]
        
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_size,
            chunk_overlap=parent_overlap,
            separators=self.separators,
            keep_separator=True
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size,
            chunk_overlap=child_overlap,
            separators=self.separators,
            keep_separator=True
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into hierarchical parent-child chunks.
        
        Returns a list of child documents, each containing parent context in metadata.
        """
        all_child_docs = []
        for doc in documents:
            child_docs = self.split_text(doc.page_content, doc.metadata)
            all_child_docs.extend(child_docs)
        return all_child_docs
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Split text into parent-child chunks."""
        if metadata is None:
            metadata = {}
            
        # 1. Split into parents
        parents = self.parent_splitter.split_text(text)
        
        all_children = []
        for i, parent_text in enumerate(parents):
            # 2. Split parent into children
            children = self.child_splitter.split_text(parent_text)
            
            for j, child_text in enumerate(children):
                # Create a copy of metadata to avoid side effects
                child_metadata = metadata.copy()
                child_metadata.update({
                    "parent_chunk_id": i,
                    "child_chunk_id": j,
                    "parent_content": parent_text,
                    "is_hierarchical": True
                })
                
                all_children.append(Document(
                    page_content=child_text,
                    metadata=child_metadata
                ))
                
        return all_children
    
    def _get_chunks(self, text: str) -> List[str]:
        """Implementation for BaseChunker compatibility. 
        Note: This loses the parent metadata as it only returns strings.
        Use split_text or split_documents instead.
        """
        # Fallback to child splitting
        return self.child_splitter.split_text(text)
