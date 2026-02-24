"""
Tests for RAG connector functionality
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.retrieval.rag_connector import RAGConnector
from src.models.session_model import SessionManager

@pytest.fixture
def mock_vectorstore():
    """Create a mock vector store."""
    vectorstore = Mock()
    vectorstore.as_retriever.return_value = Mock()
    return vectorstore

@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    return Mock(spec=SessionManager)

@pytest.fixture
def rag_connector(mock_vectorstore, mock_session_manager):
    """Create a RAG connector instance with mocked dependencies."""
    with patch.dict('os.environ', {'GROQ_API_KEY': 'dummy_key'}):
        return RAGConnector(mock_vectorstore, mock_session_manager)

def test_initialize_llm_missing_key():
    """Test LLM initialization with missing API key."""
    with patch.dict('os.environ', clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            RAGConnector(Mock(), Mock())
        assert "GROQ_API_KEY not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_process_question_missing_data(rag_connector):
    """Test processing question with missing data."""
    with pytest.raises(HTTPException) as exc_info:
        await rag_connector.process_question({})
    assert exc_info.value.status_code == 400
    assert "Session ID and question are required" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_process_question_success(rag_connector, mock_session_manager):
    """Test successful question processing."""
    # Mock session history
    mock_history = Mock()
    mock_session_manager.get_session_history.return_value = mock_history
    
    # Mock RAG chain response
    rag_connector.rag_chain = Mock()
    mock_response = {
        "answer": "Test answer",
        "context": [
            Mock(metadata={
                "source": "test.pdf",
                "page": 1,
                "type": "text"
            })
        ]
    }
    rag_connector.rag_chain.invoke.return_value = mock_response
    
    # Process question
    result = await rag_connector.process_question({
        "session_id": "test_session",
        "question": "test question"
    })
    
    # Verify response
    assert isinstance(result, JSONResponse)
    content = result.body.decode()
    assert "test_session" in content
    assert "Test answer" in content
    assert "test.pdf" in content

def test_extract_sources(rag_connector):
    """Test source extraction from documents."""
    # Create mock documents
    docs = [
        Mock(metadata={
            "source": "/path/to/doc1.pdf",
            "page": 1,
            "type": "text"
        }),
        Mock(metadata={
            "source": "/path/to/doc2.pdf",
            "page": 2,
            "type": "table"
        })
    ]
    
    sources = rag_connector._extract_sources(docs)
    
    assert len(sources) == 2
    assert sources[0]["source"] == "doc1.pdf"
    assert sources[0]["page"] == 1
    assert sources[0]["type"] == "text"
    assert sources[1]["source"] == "doc2.pdf"
    assert sources[1]["page"] == 2
    assert sources[1]["type"] == "table" 