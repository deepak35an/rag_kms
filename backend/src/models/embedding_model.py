"""
Embedding model implementation for the RAG system.

This module provides the EmbeddingModel class which handles:
- Initialization of SentenceTransformers (Native)
- Environment configuration for model access
- Embedding retrieval

Classes:
    EmbeddingModel: Main class for managing document embeddings
"""
import os
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer



logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    Manages document embeddings for the RAG system using SentenceTransformers directly.
    """
    def __init__(self):
        """
        Initialize the embedding model with native SentenceTransformer.
        """
        load_dotenv()
        # HF Token check kept for compatibility/verification, though S-T usually works without it for public models
        self.hf_token = os.getenv("HF_TOKEN")
        if not self.hf_token:
             logger.warning("HF_TOKEN not found. Public models may still work, but gated models will fail.")
        
        self.model = self._initialize_embeddings()
        # Add dimension property for vector store synchronization
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def _initialize_embeddings(self):
        """
        Initialize the SentenceTransformer model.
        
        Returns:
            SentenceTransformer: Configured embedding model instance
        """
        # Using CPU for stability as per requirements
        return SentenceTransformer("all-MiniLM-L12-v2", device="cpu")

    
    @property
    def embeddings(self):
        """Backwards compatibility property"""
        return self
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of documents.
        Required signature for Qdrant compatibility.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=False, convert_to_tensor=False)
        # Ensure it returns list of lists given the encoder might return numpy array
        return [e.tolist() if hasattr(e, "tolist") else e for e in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a single query.
        """
        embedding = self.model.encode(text, convert_to_numpy=False, convert_to_tensor=False)
        return embedding.tolist() if hasattr(embedding, "tolist") else embedding

