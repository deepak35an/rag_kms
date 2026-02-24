"""
Tests for session management functionality
"""
import pytest
from fastapi import HTTPException
from src.models.session_model import SessionManager

def test_create_session():
    """Test creating a new session."""
    manager = SessionManager()
    result = manager.create_session()
    
    assert "session_id" in result
    assert isinstance(result["session_id"], str)
    assert len(result["session_id"]) > 0

def test_get_session_history_valid():
    """Test getting history for a valid session."""
    manager = SessionManager()
    session = manager.create_session()
    session_id = session["session_id"]
    
    history = manager.get_session_history(session_id)
    assert history is not None
    assert len(history.messages) == 0

def test_get_session_history_invalid():
    """Test getting history for an invalid session."""
    manager = SessionManager()
    
    with pytest.raises(HTTPException) as exc_info:
        manager.get_session_history("invalid_session_id")
    assert exc_info.value.status_code == 404
    assert "Session ID not found" in str(exc_info.value.detail)

def test_update_session_history():
    """Test updating session history with messages."""
    manager = SessionManager()
    session = manager.create_session()
    session_id = session["session_id"]
    
    # Add messages to history
    user_input = "Test question"
    ai_response = "Test answer"
    manager.update_session_history(session_id, user_input, ai_response)
    
    # Verify messages were added
    history = manager.get_session_history(session_id)
    messages = history.messages
    assert len(messages) == 2
    assert messages[0].content == user_input
    assert messages[1].content == ai_response 