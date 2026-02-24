"""
Tests for the vector store
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document
from src.retrieval.vector_store import VectorStore

@pytest.fixture
def mock_embedding_function():
    """Create a mock embedding function."""
    return Mock()

@pytest.fixture
def vector_store(mock_embedding_function):
    """Create a vector store instance with mock embedding function."""
    return VectorStore(mock_embedding_function)

def test_vector_store_initialization(vector_store, mock_embedding_function):
    """Test vector store initialization."""
    assert vector_store.embedding_function == mock_embedding_function
    assert vector_store.persist_directory == "./chroma_db"
    assert vector_store.vectorstore is None

def test_create_or_load(vector_store):
    """Test creating or loading vector store."""
    with patch('langchain_community.vectorstores.Chroma') as mock_chroma:
        vectorstore = vector_store.create_or_load()
        mock_chroma.assert_called_once_with(
            embedding_function=vector_store.embedding_function,
            persist_directory=vector_store.persist_directory
        )
        assert vectorstore == mock_chroma.return_value

def test_add_documents(vector_store):
    """Test adding documents to vector store."""
    # Create mock documents
    docs = [
        Document(page_content="Test content 1", metadata={"source": "test1.pdf"}),
        Document(page_content="Test content 2", metadata={"source": "test2.pdf"})
    ]
    
    with patch('langchain_community.vectorstores.Chroma') as mock_chroma, \
         patch('langchain_text_splitters.RecursiveCharacterTextSplitter') as mock_splitter:
        # Setup mock splitter
        mock_splitter.return_value.split_documents.return_value = docs
        
        # Add documents
        vectorstore = vector_store.add_documents(docs, batch_size=1)
        
        # Verify splitter was called correctly
        mock_splitter.assert_called_once()
        mock_splitter.return_value.split_documents.assert_called_once_with(docs)
        
        # Verify documents were added in batches
        mock_instance = mock_chroma.return_value
        assert mock_instance.add_documents.call_count == 2
        mock_instance.add_documents.assert_any_call([docs[0]])
        mock_instance.add_documents.assert_any_call([docs[1]])

def test_get_vectorstore_creates_if_none(vector_store):
    """Test getting vector store creates one if none exists."""
    with patch('langchain_community.vectorstores.Chroma') as mock_chroma:
        vectorstore = vector_store.get_vectorstore()
        mock_chroma.assert_called_once()
        assert vectorstore == mock_chroma.return_value

def test_get_vectorstore_returns_existing(vector_store):
    """Test getting vector store returns existing one."""
    with patch('langchain_community.vectorstores.Chroma') as mock_chroma:
        # Create vector store first
        vector_store.create_or_load()
        mock_chroma.reset_mock()
        
        # Get vector store
        vectorstore = vector_store.get_vectorstore()
        mock_chroma.assert_not_called()
        assert vectorstore == vector_store.vectorstore 