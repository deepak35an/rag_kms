"""Hybrid Chunking Strategy for RAG4GOV.

This module implements a hybrid chunking strategy that combines multiple approaches
to create optimal chunks for different document types and content structures.
"""

import logging
import re
from typing import List, Dict, Optional, Any, Callable, Union
from langchain_core.documents import Document
from ..chunking import BaseChunker
from .recursive_chunker import RecursiveChunker
from .semantic_chunker import SemanticChunker
from .fixed_size_chunker import FixedSizeChunker

logger = logging.getLogger(__name__)

class HybridChunker(BaseChunker):
    """Hybrid chunker that combines multiple chunking strategies."""
    
    def __init__(self, embedding_function: Optional[Callable] = None, 
                 chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the hybrid chunker.
        
        Args:
            embedding_function: Function to generate embeddings for semantic chunking
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        super().__init__(chunk_size, chunk_overlap)
        self.embedding_function = embedding_function
        
        # Initialize different chunkers
        self.recursive_chunker = RecursiveChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.fixed_size_chunker = FixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize semantic chunker if embedding function is provided
        self.semantic_chunker = None
        if embedding_function:
            self.semantic_chunker = SemanticChunker(
                embedding_function=embedding_function,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents using the appropriate chunking strategy.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        result = []
        
        # Group documents by type
        text_docs = []
        table_docs = []
        structured_docs = []
        
        for doc in documents:
            doc_type = doc.metadata.get("type", "")
            
            if doc_type == "table":
                table_docs.append(doc)
            elif doc_type == "structured" or "form" in doc_type.lower():
                structured_docs.append(doc)
            else:
                text_docs.append(doc)
        
        # Process each document type with the appropriate chunker
        
        # Tables - preserve structure with minimal chunking
        if table_docs:
            logger.info(f"Processing {len(table_docs)} table documents with fixed-size chunker")
            # Don't split tables at all to preserve structure
            result.extend(table_docs)
        
        # Structured documents - use recursive chunking with custom separators
        if structured_docs:
            logger.info(f"Processing {len(structured_docs)} structured documents with recursive chunker")
            # Use recursive chunker with larger chunk size for structured data
            structured_chunker = RecursiveChunker(
                chunk_size=self.chunk_size * 2,  # Larger chunks for structured data
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ";", ":"]  # Limited separators for structured data
            )
            result.extend(structured_chunker.split_documents(structured_docs))
        
        # Text documents - use semantic chunking if available, otherwise recursive
        if text_docs:
            if self.semantic_chunker:
                logger.info(f"Processing {len(text_docs)} text documents with semantic chunker")
                result.extend(self.semantic_chunker.split_documents(text_docs))
            else:
                logger.info(f"Processing {len(text_docs)} text documents with recursive chunker")
                result.extend(self.recursive_chunker.split_documents(text_docs))
        
        return result
    
    def _get_chunks(self, text: str) -> List[str]:
        """Get chunks from text using the appropriate chunking strategy.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Detect document type based on content
        is_table = self._is_table_content(text)
        is_structured = self._is_structured_content(text)
        
        if is_table:
            # For table content, preserve structure
            return [text]
        elif is_structured:
            # For structured content, use recursive chunking with limited separators
            return self.recursive_chunker._get_chunks(text)
        else:
            # For regular text, use semantic chunking if available
            if self.semantic_chunker:
                return self.semantic_chunker._get_chunks(text)
            else:
                return self.recursive_chunker._get_chunks(text)
    
    def _is_table_content(self, text: str) -> bool:
        """Detect if content is likely a table."""
        # Simple heuristic: tables often have consistent line lengths and delimiter patterns
        lines = text.strip().split('\n')
        if len(lines) < 3:  # Too few lines to be a table
            return False
            
        # Check for JSON table format
        if text.strip().startswith('{') and 'rows' in text:
            return True
            
        # Check for delimiter consistency (e.g., |, \t, or multiple spaces)
        delimiters = ['|', '\t']
        for delimiter in delimiters:
            if all(delimiter in line for line in lines[:5]):
                return True
                
        # Check for consistent line lengths and spacing patterns
        line_lengths = [len(line) for line in lines[:5]]
        if max(line_lengths) - min(line_lengths) < 5:  # Very consistent line lengths
            return True
            
        return False
    
    def _is_structured_content(self, text: str) -> bool:
        """Detect if content has structured format (forms, lists, etc.)."""
        # Check for form-like patterns
        form_patterns = [
            r'\w+\s*:\s*\w+',  # Key: Value pattern
            r'\d+\.\s+\w+',    # Numbered list
            r'•\s+\w+',        # Bullet points
        ]
        
        for pattern in form_patterns:
            if re.search(pattern, text):
                return True
                
        # Check for consistent indentation patterns
        lines = text.strip().split('\n')
        indentation_levels = set()
        for line in lines:
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indentation_levels.add(leading_spaces)
        
        # Multiple consistent indentation levels suggest structured content
        if len(indentation_levels) > 1 and len(indentation_levels) <= 4:
            return True
            
        return False