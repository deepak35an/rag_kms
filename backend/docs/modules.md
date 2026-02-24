# RAG4GOV Modules Documentation

## Preprocessing Module

### DocumentProcessor
```python
from preprocessing import document_processor

# Process PDFs in a directory
documents = document_processor.process_pdfs("./pdfs/")

# Download and process from Google Drive
document_processor.download_pdf("https://drive.google.com/file/...")
```

Key features:
- PDF text and table extraction
- OCR support for scanned documents
- Archive file handling (ZIP, TAR)
- Google Drive integration

### DataFetcher
```python
from preprocessing.data_fetch import data_fetcher

# Download from Google Drive
file_path = data_fetcher.download_from_drive(drive_link, destination_folder)
```

## Models Module

### EmbeddingModel
```python
from models.embedding_model import EmbeddingModel

embedding_model = EmbeddingModel()
embeddings = embedding_model.get_embeddings()
```

### SessionManager
```python
from models.session_model import SessionManager

session_manager = SessionManager()
session = session_manager.create_session()
history = session_manager.get_session_history(session["session_id"])
```

### RAGModel
```python
from models.rag_model import RAGModel

rag_model = RAGModel(vectorstore)
chain = rag_model.get_chain()
```

## Retrieval Module

### VectorStore
```python
from retrieval.vector_store import VectorStore

vector_store = VectorStore(embedding_function)
vectorstore = vector_store.add_documents(documents)
```

### RAGConnector
```python
from retrieval.rag_connector import RAGConnector

connector = RAGConnector(vectorstore, session_manager)
response = await connector.process_question({
    "session_id": "...",
    "question": "..."
})
```

## Generation Module

### Generator
```python
from generation.generator import Generator

generator = Generator(rag_model, session_manager)
response = await generator.generate_response({
    "session_id": "...",
    "question": "..."
})
```

## API Usage

### Main Application
```python
from fastapi import FastAPI
from main import app

# Create session
POST /create_session
Response: {"session_id": "..."}

# Ask question
POST /ask
Request: {
    "session_id": "...",
    "question": "..."
}
Response: {
    "session_id": "...",
    "question": "...",
    "response": "...",
    "sources": [...]
}

# Download document
POST /download
Request: {
    "drive_link": "..."
}
```

## Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token

# Optional
LOG_LEVEL=INFO
```

### Directory Structure
```
src/
├── preprocessing/
│   ├── __init__.py
│   ├── preprocessing.py
│   └── data_fetch.py
├── models/
│   ├── embedding_model.py
│   ├── rag_model.py
│   └── session_model.py
├── retrieval/
│   ├── rag_connector.py
│   └── vector_store.py
├── generation/
│   └── generator.py
└── main.py
```
