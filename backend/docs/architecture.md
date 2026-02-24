# RAG4GOV System Architecture

## Overview
RAG4GOV is a Retrieval-Augmented Generation (RAG) system designed to provide accurate information about the Joint Admission Committee (JAC) Chandigarh. The system combines document retrieval with language model generation to deliver context-aware responses to user queries.

## Core Components

### 1. Document Processing (`preprocessing/`)
- **DocumentProcessor**: Handles PDF document processing
  - Text extraction using `pdfplumber`
  - Table extraction and formatting
  - OCR fallback using `pytesseract`
  - PDF integrity checking
- **DataFetcher**: Manages document downloads
  - Google Drive integration
  - Support for PDF, ZIP, and TAR archives

### 2. Embedding and Vector Storage (`models/`, `retrieval/`)
- **EmbeddingModel**: Generates document embeddings
  - Uses HuggingFace's "all-MiniLM-L6-v2" model
  - Requires HuggingFace API token
- **VectorStore**: Manages document vectors
  - Uses Chroma for vector storage
  - Implements batch processing
  - Handles document chunking and overlap

### 3. RAG System (`models/`, `retrieval/`, `generation/`)
- **RAGModel**: Core RAG implementation
  - Context-aware question formulation
  - Document retrieval
  - Answer generation using Groq's Gemma 2 9B model
- **Generator**: Response generation
  - Manages conversation flow
  - Handles source attribution
  - Error handling and logging

### 4. Session Management (`models/`)
- **SessionManager**: Manages user sessions
  - UUID-based session creation
  - Chat history tracking
  - Conversation context maintenance

### 5. API Layer (`main.py`)
- FastAPI-based REST API
- Endpoints:
  - `/create_session`: Initialize new chat sessions
  - `/ask`: Process questions and generate responses
  - `/download`: Handle document downloads

## Data Flow

1. **Document Ingestion**:
   ```
   PDF/Archive → DocumentProcessor → Chunks → EmbeddingModel → VectorStore
   ```

2. **Query Processing**:
   ```
   User Query → SessionManager → RAGModel → [Retriever → Generator] → Response
   ```

3. **Response Generation**:
   ```
   Retrieved Docs + Query → LLM → Generated Answer + Sources
   ```

## System Requirements

- Python 3.8+
- Environment Variables:
  - `GROQ_API_KEY`: For LLM access
  - `HF_TOKEN`: For embedding model
- Storage:
  - Local storage for PDFs (`./public/`)
  - Vector store persistence (`./chroma_db/`)

## Error Handling

The system implements comprehensive error handling:
- PDF processing fallbacks (OCR)
- API error responses (400, 404, 500)
- Logging at multiple levels
- Graceful degradation for malformed tables

## Security Considerations

- API key management
- Session-based access
- Safe file handling
- Input validation
- Secure document storage
