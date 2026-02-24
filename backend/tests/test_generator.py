"""
Tests for the response generator
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.generation.generator import Generator

@pytest.fixture
def mock_rag_model():
    """Create a mock RAG model."""
    rag_model = Mock()
    rag_model.get_chain.return_value = Mock()
    return rag_model

@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    session_manager = Mock()
    session_manager.get_session_history.return_value = Mock()
    return session_manager

@pytest.fixture
def generator(mock_rag_model, mock_session_manager):
    """Create a Generator instance with mock dependencies."""
    return Generator(mock_rag_model, mock_session_manager)

@pytest.mark.asyncio
async def test_generate_response_missing_data(generator):
    """Test generating response with missing data."""
    with pytest.raises(HTTPException) as exc_info:
        await generator.generate_response({})
    assert exc_info.value.status_code == 400
    assert "Session ID and question are required" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_generate_response_success(generator, mock_session_manager):
    """Test successful response generation."""
    # Mock chain response
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
    generator.rag_model.get_chain().invoke.return_value = mock_response

    # Generate response
    result = await generator.generate_response({
        "session_id": "test_session",
        "question": "test question"
    })

    # Verify response
    assert isinstance(result, JSONResponse)
    content = result.body.decode()
    assert "test_session" in content
    assert "Test answer" in content
    assert "test.pdf" in content

    # Verify session history was updated
    mock_session_manager.update_session_history.assert_called_once_with(
        "test_session", "test question", "Test answer"
    )

@pytest.mark.asyncio
async def test_generate_response_error(generator):
    """Test error handling during response generation."""
    generator.rag_model.get_chain().invoke.side_effect = Exception("Test error")

    with pytest.raises(HTTPException) as exc_info:
        await generator.generate_response({
            "session_id": "test_session",
            "question": "test question"
        })
    assert exc_info.value.status_code == 500
    assert "Test error" in str(exc_info.value.detail)

def test_extract_sources(generator):
    """Test extraction of source information from documents."""
    mock_docs = [
        Mock(metadata={
            "source": "/path/to/test1.pdf",
            "page": 1,
            "type": "text"
        }),
        Mock(metadata={
            "source": "/path/to/test2.pdf",
            "page": 2,
            "type": "table"
        })
    ]

    sources = generator._extract_sources(mock_docs)

    assert len(sources) == 2
    assert sources[0] == {
        "source": "test1.pdf",
        "page": 1,
        "type": "text"
    }
    assert sources[1] == {
        "source": "test2.pdf",
        "page": 2,
        "type": "table"
    } 