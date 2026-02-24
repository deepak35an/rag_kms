# RAG4GOV

[![Release](https://img.shields.io/github/v/release/laleye/rag4gov)](https://img.shields.io/github/v/release/laleye/rag4gov)
[![Build status](https://img.shields.io/github/actions/workflow/status/laleye/rag4gov/main.yml?branch=main)](https://github.com/laleye/rag4gov/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/laleye/rag4gov)](https://img.shields.io/github/commit-activity/m/laleye/rag4gov)
[![License](https://img.shields.io/github/license/laleye/rag4gov)](https://img.shields.io/github/license/laleye/rag4gov)

## Overview

RAG4GOV is a Retrieval-Augmented Generation system designed to provide accurate and context-aware responses to queries about the Joint Admission Committee (JAC) Chandigarh. The system combines advanced document processing, vector-based retrieval, and state-of-the-art language models to deliver precise information from official documentation.

## Features

- **Smart Document Processing**
  - PDF text and table extraction
  - OCR support for scanned documents
  - Google Drive integration
  - Archive file handling (ZIP, TAR)

- **Advanced RAG Implementation**
  - Context-aware question answering
  - Conversation history tracking
  - Source attribution for responses
  - Efficient vector-based retrieval

- **Modern API Design**
  - FastAPI-based REST endpoints
  - Session management
  - Async request handling
  - Comprehensive error handling

## Quick Start

1. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/laleye/rag4gov.git
   cd rag4gov

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   # Create .env file
   cp .env.example .env

   # Add your API keys
   GROQ_API_KEY=your_groq_api_key
   HF_TOKEN=your_huggingface_token
   ```

3. **Run the Application**
   ```bash
   # Start the FastAPI server
   uvicorn src.main:app --reload
   ```

4. **Access the API**
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## Usage Examples

1. **Create a Session**
   ```bash
   curl -X POST http://localhost:8000/create_session
   ```

2. **Ask a Question**
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your_session_id",
       "question": "What are the eligibility criteria for JAC admissions?"
     }'
   ```

3. **Download a Document**
   ```bash
   curl -X POST http://localhost:8000/download \
     -H "Content-Type: application/json" \
     -d '{
       "drive_link": "https://drive.google.com/file/..."
     }'
   ```

## Project Structure

```
rag4gov/
├── src/               # Source code
├── tests/             # Test files
├── docs/              # Documentation
├── public/            # PDF storage
├── chroma_db/         # Vector store
├── requirements.txt   # Dependencies
└── README.md         # Project readme
```

## Development

1. **Setup Development Environment**
   ```bash
   # Install dev dependencies
   pip install -r requirements-dev.txt

   # Setup pre-commit hooks
   pre-commit install
   ```

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Code Quality**
   ```bash
   # Run linter
   flake8 src/

   # Run type checker
   mypy src/
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Documentation

- [Architecture Overview](architecture.md)
- [Module Documentation](modules.md)
- [API Reference](https://rag4gov.readthedocs.io/)
