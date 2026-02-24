"""
Response generation module for the RAG4GOV system.

This module contains the Generator class which handles:
- Response generation from retrieved documents
- Session-based conversation history
- Error handling and validation
- Cosine similarity search for improved relevance scoring

Classes:
    Generator: Main class for generating responses with RAG model integration
"""
import logging
import asyncio
from typing import Dict, List, Any
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.runnables.history import RunnableWithMessageHistory
from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class Generator:
    """
    Response generator for the RAG4GOV system.
    
    Attributes:
        rag_model: The RAG model instance for document retrieval
        session_manager: Session manager for conversation history
        vectorizer: TF-IDF vectorizer for cosine similarity calculation
    """
    def __init__(self, rag_model, session_manager):
        """
        Initialize the generator with RAG model and session manager.
        
        Args:
            rag_model: The RAG model instance
            session_manager: Session manager instance
        """
        self.rag_model = rag_model
        self.session_manager = session_manager
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')

    async def generate_response(self, data: Dict[str, str]) -> JSONResponse:
        """
        Generate a response for the user's question.
        
        Args:
            data: Dictionary containing 'session_id' and 'question'
            
        Returns:
            JSONResponse: Contains generated answer or error message
            
        Raises:
            HTTPException: If session_id or question is missing
        """
        session_id = data.get("session_id")
        user_input = data.get("question")

        if not session_id or not user_input:
            raise HTTPException(status_code=400, detail="Session ID and question are required.")

        session_history = self.session_manager.get_session_history(session_id)
        logger.info(f"Generating response for session {session_id}: {user_input[:50]}...")

        try:
            # Create conversational chain with message history
            conversational_rag_chain = RunnableWithMessageHistory(
                self.rag_model.get_chain(user_input),
                lambda session: session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )

            # Get response with retrieved documents
            response = await conversational_rag_chain.ainvoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )

            answer = response.get("answer", "Currently, this information is not available.")
            retrieved_docs = response.get("context", [])
            
            # Safety check: ensure retrieved_docs is not a coroutine
            if asyncio.iscoroutine(retrieved_docs):
                logger.error("CRITICAL: retrieved_docs is a coroutine, not a list. Async pipeline error.")
                retrieved_docs = await retrieved_docs # Emergency await
            
            # Log retrieved documents for debugging
            for i, doc in enumerate(retrieved_docs):
                logger.debug(f"Retrieved doc {i}: page={doc.metadata.get('page')}, source={doc.metadata.get('source')}, content={doc.page_content[:50]}...")

            # Apply cosine similarity for better relevance scoring
            validated_docs = self._validate_retrieved_docs_with_cosine(retrieved_docs, user_input)
            
            # Extract source information from validated documents
            sources = self._extract_sources(validated_docs)

            # Update session history
            self.session_manager.update_session_history(session_id, user_input, answer)

            logger.info(f"Successfully generated response for session {session_id}")

            return JSONResponse(content={
                "session_id": session_id,
                "question": user_input,
                "response": answer,
                "sources": sources
            })

        except Exception as e:
            logger.error(f"Error generating response for session {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _extract_sources(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved markdown documents."""
        sources = []
        for doc in documents:
            metadata = doc.metadata
            source_file = metadata.get("original_source", metadata.get("source", "Unknown source"))
            
            # Validate page number
            page = metadata.get("page")
            if page is None:
                logger.warning(f"Page number missing for document from {source_file}. Defaulting to 1.")
                page = 1
            elif not isinstance(page, int) or page < 1:
                logger.warning(f"Invalid page number {page} for {source_file}. Defaulting to 1.")
                page = 1

            # Check for table-specific metadata
            table_number = metadata.get("table_number")
            content_type = "table" if table_number is not None else metadata.get("type", "text")

            source_info = {
                "source": source_file,
                "type": content_type,
                "relevance": metadata.get("relevance_score", 1.0),
                "content_preview": doc.page_content[:200],
                "page": page,
                "section": metadata.get("section", ""),
            }
            
            if table_number is not None:
                source_info["table_number"] = table_number

            sources.append(source_info)
        
        return sorted(sources, key=lambda x: x["relevance"], reverse=True)

    def _calculate_cosine_similarity(self, query: str, documents: List[str]) -> List[float]:
        """
        Calculate cosine similarity between query and documents using TF-IDF.
        
        Args:
            query: User query string
            documents: List of document content strings
            
        Returns:
            List of similarity scores
        """
        try:
            # Handle empty documents list
            if not documents:
                return []
                
            # Create a combined corpus with query and documents
            corpus = [query] + documents
            
            # Fit and transform the corpus
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity between query (first element) and all documents
            query_vector = tfidf_matrix[0:1]
            document_vectors = tfidf_matrix[1:]
            
            # Calculate similarity scores
            cosine_scores = cosine_similarity(query_vector, document_vectors).flatten()
            
            return cosine_scores.tolist()
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            # Return default scores if calculation fails
            return [0.5] * len(documents)

    def _validate_retrieved_docs_with_cosine(self, documents: List[Any], query: str) -> List[Any]:
        """
        Validate and score retrieved documents using cosine similarity and content relevance.
        
        Args:
            documents: List of retrieved document objects
            query: User query string
            
        Returns:
            List of validated and scored document objects
        """
        if not documents:
            logger.warning("No documents retrieved for validation")
            return []
            
        # Extract document contents
        doc_contents = [doc.page_content for doc in documents]
        
        # Calculate cosine similarity scores
        cosine_scores = self._calculate_cosine_similarity(query, doc_contents)
        
        validated_docs = []
        for i, doc in enumerate(documents):
            # Apply cosine similarity score
            if i < len(cosine_scores):
                doc.metadata["relevance_score"] = cosine_scores[i]
            else:
                doc.metadata["relevance_score"] = 0.0
                logger.warning(f"Mismatched index in cosine scores for document {i}")
            
            # Log page number issues
            page = doc.metadata.get("page")
            if page is None or not isinstance(page, int) or page < 1:
                logger.debug(f"Invalid or missing page number in doc from {doc.metadata.get('source', 'unknown')}: {page}")
            
            # Apply threshold for document inclusion
            if doc.metadata["relevance_score"] > 0.1:
                validated_docs.append(doc)
        
        # Sort documents by relevance score
        validated_docs.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
        
        # Log similarity scores for top documents
        for i, doc in enumerate(validated_docs[:3] if len(validated_docs) >= 3 else validated_docs):
            logger.debug(f"Top doc {i}: relevance={doc.metadata.get('relevance_score', 0):.4f}, "
                         f"source={doc.metadata.get('source', 'unknown')}")
        
        return validated_docs

    def _validate_retrieved_docs(self, documents: List[Any], query: str) -> List[Any]:
        """
        Legacy method for keyword-based validation.
        Now redirects to cosine similarity implementation.
        """
        logger.info("Using cosine similarity for document relevance scoring")
        return self._validate_retrieved_docs_with_cosine(documents, query)