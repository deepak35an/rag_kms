"""Semantic Chunking Strategies for RAG4GOV

This module provides a unified interface to different chunking strategies:
1. Fixed-size chunking: Simple character-based chunking with fixed size
2. Recursive chunking: Hierarchical chunking based on separators
3. Semantic chunking: Embedding-based chunking that preserves meaning
4. Hybrid chunking: Combines multiple strategies for optimal results

Usage:
    from preprocessing.chunking_strategies import get_chunker
    
    # Get a specific chunker
    chunker = get_chunker('semantic', embedding_function=embeddings.embed_query)
    
    # Split documents
    chunks = chunker.split_documents(documents)
"""

import logging
from typing import List, Dict, Optional, Any, Callable, Union
from langchain_core.documents import Document

# Import chunkers
from .chunking import BaseChunker
from .chunkers.fixed_size_chunker import FixedSizeChunker
from .chunkers.recursive_chunker import RecursiveChunker
from .chunkers.semantic_chunker import SemanticChunker
from .chunkers.hybrid_chunker import HybridChunker
from .chunkers.hierarchical_chunker import HierarchicalChunker

logger = logging.getLogger(__name__)

def get_chunker(chunker_type: str, 
               embedding_function: Optional[Callable] = None,
               chunk_size: int = 1000, 
               chunk_overlap: int = 200,
               **kwargs) -> BaseChunker:
    """Get a chunker instance based on the specified type.
    
    Args:
        chunker_type: Type of chunker to use ('fixed', 'recursive', 'semantic', 'hybrid')
        embedding_function: Function to generate embeddings (required for semantic and hybrid)
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
        **kwargs: Additional arguments for specific chunkers
        
    Returns:
        An instance of the specified chunker
        
    Raises:
        ValueError: If an invalid chunker type is specified
    """
    chunker_type = chunker_type.lower()
    
    if chunker_type == 'fixed':
        return FixedSizeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    elif chunker_type == 'recursive':
        separators = kwargs.get('separators', None)
        return RecursiveChunker(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            separators=separators
        )
    
    elif chunker_type == 'semantic':
        if not embedding_function:
            raise ValueError("Embedding function is required for semantic chunking")
        
        similarity_threshold = kwargs.get('similarity_threshold', 0.75)
        return SemanticChunker(
            embedding_function=embedding_function,
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            similarity_threshold=similarity_threshold
        )
    
    elif chunker_type == 'hybrid':
        return HybridChunker(
            embedding_function=embedding_function,
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
    
    elif chunker_type == 'hierarchical':
        parent_size = kwargs.get('parent_size', 1500)
        parent_overlap = kwargs.get('parent_overlap', 200)
        child_size = kwargs.get('child_size', chunk_size)
        child_overlap = kwargs.get('child_overlap', chunk_overlap)
        return HierarchicalChunker(
            parent_size=parent_size,
            parent_overlap=parent_overlap,
            child_size=child_size,
            child_overlap=child_overlap
        )
    
    else:
        raise ValueError(f"Unknown chunker type: {chunker_type}")

# Default chunker types for different document types
DOCUMENT_TYPE_CHUNKERS = {
    'text': 'recursive',  # Default for text documents
    'table': 'fixed',     # Tables should be preserved as much as possible
    'structured': 'recursive',  # Structured documents like forms
    'code': 'recursive',  # Code documents
    'default': 'recursive'  # Default fallback
}

def get_chunker_for_document_type(doc_type: str, 
                                 embedding_function: Optional[Callable] = None,
                                 chunk_size: int = 1000, 
                                 chunk_overlap: int = 200,
                                 **kwargs) -> BaseChunker:
    """Get the appropriate chunker for a specific document type.
    
    Args:
        doc_type: Type of document ('text', 'table', 'structured', 'code')
        embedding_function: Function to generate embeddings
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
        **kwargs: Additional arguments for specific chunkers
        
    Returns:
        An instance of the appropriate chunker for the document type
    """
    chunker_type = DOCUMENT_TYPE_CHUNKERS.get(doc_type.lower(), DOCUMENT_TYPE_CHUNKERS['default'])
    
    # If embedding function is available, use semantic chunking for text documents
    if doc_type.lower() == 'text' and embedding_function is not None:
        chunker_type = 'semantic'
    
    return get_chunker(
        chunker_type=chunker_type,
        embedding_function=embedding_function,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )