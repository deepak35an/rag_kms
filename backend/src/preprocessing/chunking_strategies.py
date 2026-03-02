"""Chunking Strategies for RAG4GOV

This module provides a unified interface to the hierarchical chunking strategy
used in production. Other strategies (fixed, recursive, semantic, hybrid) are
retained as separate files for reference but are not part of the active pipeline.

Usage:
    from preprocessing.chunking_strategies import get_chunker

    chunker = get_chunker('hierarchical')
    chunks = chunker.split_documents(documents)
"""

import logging
from typing import List, Optional, Callable
from langchain_core.documents import Document

from .chunking import BaseChunker
from .chunkers.hierarchical_chunker import HierarchicalChunker

logger = logging.getLogger(__name__)


def get_chunker(
    chunker_type: str = 'hierarchical',
    embedding_function: Optional[Callable] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    **kwargs
) -> BaseChunker:
    """Return a chunker instance.

    Only 'hierarchical' is used in production. Passing any other type will
    raise a ValueError so that accidental misuse is caught early.

    Args:
        chunker_type: Must be 'hierarchical'.
        embedding_function: Unused — kept for call-site compatibility.
        chunk_size: Child chunk size (characters).
        chunk_overlap: Child chunk overlap (characters).
        **kwargs: parent_size, parent_overlap, child_size, child_overlap
                  are forwarded to HierarchicalChunker.

    Returns:
        HierarchicalChunker instance.

    Raises:
        ValueError: If an unsupported chunker type is requested.
    """
    if chunker_type.lower() != 'hierarchical':
        raise ValueError(
            f"Unsupported chunker type '{chunker_type}'. "
            "Only 'hierarchical' is supported in production. "
            "See src/preprocessing/chunkers/ for other implementations."
        )

    parent_size = kwargs.get('parent_size', 1500)
    parent_overlap = kwargs.get('parent_overlap', 200)
    child_size = kwargs.get('child_size', chunk_size)
    child_overlap = kwargs.get('child_overlap', chunk_overlap)

    return HierarchicalChunker(
        parent_size=parent_size,
        parent_overlap=parent_overlap,
        child_size=child_size,
        child_overlap=child_overlap,
    )


def get_chunker_for_document_type(
    doc_type: str,
    embedding_function: Optional[Callable] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    **kwargs
) -> BaseChunker:
    """Return the production chunker regardless of document type.

    Previously this function routed to different strategies (recursive for text,
    fixed for tables, etc.) which caused inconsistent chunk metadata.
    All document types now go through the hierarchical chunker for consistency.

    Args:
        doc_type: Ignored — kept for call-site compatibility.
        embedding_function: Ignored — kept for call-site compatibility.
        chunk_size: Child chunk size (characters).
        chunk_overlap: Child chunk overlap (characters).
        **kwargs: Forwarded to get_chunker().

    Returns:
        HierarchicalChunker instance.
    """
    if doc_type.lower() == 'table':
        logger.debug(
            "get_chunker_for_document_type called with doc_type='table'. "
            "Tables should be added as-is (no chunking). "
            "Returning hierarchical chunker as fallback."
        )
    return get_chunker(
        'hierarchical',
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )