"""
Tests for the embedding model
"""
import pytest
from unittest.mock import patch
from src.models.embedding_model import EmbeddingModel

def test_embedding_model_initialization_missing_token():
    """Test embedding model initialization with missing token."""
    with patch.dict('os.environ', clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            EmbeddingModel()
        assert "Please provide valid HuggingFace Token" in str(exc_info.value)

def test_embedding_model_initialization_success():
    """Test successful embedding model initialization."""
    with patch.dict('os.environ', {'HF_TOKEN': 'dummy_token'}):
        with patch('langchain_huggingface.HuggingFaceEmbeddings') as mock_embeddings:
            model = EmbeddingModel()
            assert model.hf_token == 'dummy_token'
            mock_embeddings.assert_called_once_with(model_name="all-MiniLM-L6-v2")

def test_get_embeddings():
    """Test getting embeddings from the model."""
    with patch.dict('os.environ', {'HF_TOKEN': 'dummy_token'}):
        with patch('langchain_huggingface.HuggingFaceEmbeddings') as mock_embeddings:
            model = EmbeddingModel()
            embeddings = model.get_embeddings()
            assert embeddings == model.embeddings
            assert embeddings == mock_embeddings.return_value 