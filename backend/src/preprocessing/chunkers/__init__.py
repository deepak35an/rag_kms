"""Chunking strategies for RAG4GOV.

Only HierarchicalChunker is active in production.
The other chunkers are retained on disk for reference only.
"""

from .hierarchical_chunker import HierarchicalChunker

# Not used in the active pipeline — kept for reference:
# from .recursive_chunker import RecursiveChunker
# from .fixed_size_chunker import FixedSizeChunker
# from .semantic_chunker import SemanticChunker
# from .hybrid_chunker import HybridChunker

__all__ = [
    'HierarchicalChunker',
]