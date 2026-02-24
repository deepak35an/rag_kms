"""
Session management model for RAG system conversations
"""
import logging
from uuid import uuid4
from langchain_community.chat_message_histories import ChatMessageHistory
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.chat_histories = {}

    def create_session(self):
        """Create a new chat session."""
        session_id = str(uuid4())
        self.chat_histories[session_id] = ChatMessageHistory()
        logger.info(f"Created new session: {session_id}")
        return {"session_id": session_id}

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get chat history for a session."""
        if session_id not in self.chat_histories:
            raise HTTPException(status_code=404, detail="Session ID not found.")
        return self.chat_histories[session_id]

    def update_session_history(self, session_id: str, user_input: str, ai_response: str):
        """Update chat history with new messages."""
        session_history = self.get_session_history(session_id)
        session_history.add_user_message(user_input)
        session_history.add_ai_message(ai_response) 