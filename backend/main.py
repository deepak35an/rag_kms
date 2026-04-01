"""
Main entry point for the RAG4GOV application.

This module initializes the FastAPI application and all RAG system components including:
- Session management
- Embedding model
- Vector store
- RAG connector
- Response generator

It also defines the API endpoints for:
- Document processing
- Question answering
- Session management

Example:
    To run the application:
    ```bash
    uvicorn main:app --reload
    ```
"""
import os

# FIX: Allow multiple OpenMP runtimes (common crash cause on Windows with Torch)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Optional: Limit threads to avoid contention
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from contextlib import asynccontextmanager
import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

from fastapi import FastAPI
from fastapi import UploadFile, File, Form
from src.preprocessing.preprocessing import document_processor
from src.preprocessing.markdown import document_processor as markdown_processor
from src.models.session_model import SessionManager
from src.models.embedding_model import EmbeddingModel
from src.retrieval.vector_store import VectorStore
# from src.retrieval.rag_gemini_connector import RAGConnector
# from src.generation.generator_gemini import Generator
# from src.retrieval.rag_ollama_connector import RAGConnector
# from src.generation.generator_ollama import Generator

from src.retrieval.rag_connector import RAGConnector
from src.generation.generator import Generator
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import shutil
import re

import asyncio
import os
from asyncio import TimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

UPLOAD_ROOT = Path(__file__).parent / "public" / "backend" / "app_uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    """Return a filesystem-safe filename/folder segment."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return cleaned or "untitled"


class DownloadRequest(BaseModel):
    """
    Pydantic model for document download requests.
    
    Attributes:
        drive_link (str): Google Drive link to the document to be processed
    """
    drive_link: str

class ChatSaveRequest(BaseModel):
    """
    Pydantic model for saving chat history.
    """
    conversation_id: str
    conversation_meta: dict
    messages: list[dict]

class IngestRequest(BaseModel):
    """
    Pydantic model for document ingestion requests.
    """
    kb_id: str

class RetrieveRequest(BaseModel):
    """
    Pydantic model for separate retrieval step.
    """
    question: str
    session_id: str
    kb_id: str

class GenerateRequest(BaseModel):
    """
    Pydantic model for separate generation step.
    """
    question: str
    session_id: str
    selected_chunks: list[dict] # Documents/chunks selected by user

# Initialize components
session_manager = SessionManager()
embedding_model = EmbeddingModel()
# Fix: use .embeddings property, not get_embeddings()
vector_store = VectorStore(embedding_model.embeddings)
rag_connector = None
generator = None
markdown_processor = markdown_processor.__class__(embedding_model.embeddings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    global rag_connector, generator
    try:
        import threading
        logger.info(f"lifespan initialized in thread: {threading.current_thread().name} ({threading.get_ident()})")
        logger.info("Initializing RAG system components...")
        
        # Initialize Embedding Model
        # embedding_model is already global
        
        # Initialize Vector Store
        # Use global vector_store initialized at module level (safely instantiated)
        
        # Initialize RAG connector
        rag_connector = RAGConnector(vector_store, session_manager)
        
        # Build BM25 index for hybrid search
        await rag_connector.initialize_hybrid_retrieval()

        # Initialize Generator
        generator = Generator(rag_connector, session_manager)
        
        logger.info("Successfully initialized RAG system components")
        yield
    except Exception as e:
        logger.error(f"Error initializing RAG system: {str(e)}")
        raise

app = FastAPI(
    title="RAG4GOV API",
    description="A RAG-based system for answering questions about JAC Chandigarh admissions",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"status": "ok", "message": "RAG4GOV API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vectorstore_loaded": rag_connector is not None,
        "generator_loaded": generator is not None
    }

@app.post("/ping")
async def ping(data: dict):
    """Ultra-simple ping endpoint for testing."""
    return {"received": data, "status": "pong"}

@app.post("/create_session")
async def create_session():
    """Create a new chat session."""
    return session_manager.create_session()

@app.post("/retrieve")
async def retrieve_only(request: RetrieveRequest):
    """Step 1: Retrieve relevant documents for a question."""
    if generator is None:
        return {"error": "Generator not initialized."}
    return await generator.retrieve_chunks(request.dict())

@app.post("/generate")
async def generate_only(request: GenerateRequest):
    """Step 2: Generate an answer using user-selected chunks."""
    if generator is None:
        return {"error": "Generator not initialized."}
    return await generator.generate_from_selected(request.dict())

@app.post("/ask")
async def ask_question(data: dict):
    """DEPRECATED: Process a question in a single step."""
    if generator is None:
        return {"error": "Generator not initialized. Server may still be starting up."}
    # For now, redirect to the legacy generation but we'll eventually move to the 2-step flow
    return await generator.generate_response(data) # type: ignore

@app.post("/test_rag")
async def test_rag(data: dict):
    """Test the RAG connector directly by returning retrieved chunks.
    
    This endpoint bypasses the generator and returns the raw chunks that would be sent to the LLM.
    Useful for testing and debugging the retrieval component.
    """
    try:
        if rag_connector is None:
            return {"error": "RAG connector not initialized. Server may still be starting up."}
        
        logger.info(f"Testing RAG with question: {data.get('question', 'N/A')}")
        result = await rag_connector.process_question(data)
        logger.info("RAG test completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in test_rag endpoint: {str(e)}", exc_info=True)
        return {"error": str(e), "type": type(e).__name__}

# ... (skip to test_simple)

@app.post("/test_simple")
async def test_simple(data: dict):
    try:
        # Use simple logging for safety
        import threading
        logger.info(f"test_simple execution thread: {threading.current_thread().name}")
        
        question = data.get("question", "")
        if not question:
            return {"error": "Question is required"}
        
        logger.info(f"Question received: {question}")

        # FIX: await the async method
        docs = await vector_store.similarity_search(question, k=5)

        logger.info(f"Docs returned type={type(docs)} len={len(docs)}")

        payload = []
        for d in docs:
            payload.append({
                "content": d.page_content[:200],
                "metadata": d.metadata
            })

        return {
            "question": question,
            "num_docs": len(payload),
            "docs": payload
        }

    except Exception as e:
        logger.error("CRASH in test_simple", exc_info=True)
        return {"error": str(e)}

@app.post("/test_embedding")
def test_embedding(data: dict):
    """Test embedding model only (no vector DB)."""
    try:
        from src.models.embedding_model import EmbeddingModel
        text = data.get("text", "Hello world")
        logger.info(f"Testing embedding for: {text}")
        
        # Initialize or use global if available (let's try new instance for isolation)
        model = EmbeddingModel()
        vector = model.embeddings.embed_query(text)
        
        return {
            "text": text,
            "vector_len": len(vector),
            "sample": vector[:5]
        }
    except Exception as e:
        logger.error(f"Error in test_embedding: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.post("/download")
async def download_document(request: DownloadRequest):
    """Download a document from Google Drive."""
    try:
        downloaded_file = markdown_processor.download_pdf(request.drive_link) # type: ignore
        return {"status": "success", "message": f"File downloaded successfully: {downloaded_file}"}
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.post("/upload_documents")
async def upload_documents(
    kb_id: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Save uploaded files to backend/public/backend/app_uploads/<kb_id>/"""
    try:
        safe_kb = _safe_name(kb_id)
        target_dir = UPLOAD_ROOT / safe_kb
        target_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for file in files:
            original_name = Path(file.filename or "untitled").name
            safe_file_name = _safe_name(original_name)

            destination = target_dir / safe_file_name
            with destination.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            saved_files.append(
                {
                    "filename": safe_file_name,
                    "original_filename": original_name,
                    "size_bytes": destination.stat().st_size,
                    "saved_path": str(destination),
                    "relative_path": str(destination.relative_to(Path(__file__).parent)),
                }
            )

        return {
            "status": "success",
            "kb_id": safe_kb,
            "upload_dir": str(target_dir),
            "files": saved_files,
        }
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    kb_id: str


@app.post("/ingest")
async def ingest_documents(request: IngestRequest):
    """
    Ingest uploaded PDFs into the Qdrant vector store.

    Pipeline: PDF → extract text (pymupdf4llm → pdfplumber → OCR) → chunk → embed → upsert.
    After ingestion, the BM25 index is rebuilt for hybrid search.
    """
    try:
        safe_kb = _safe_name(request.kb_id)
        upload_dir = UPLOAD_ROOT / safe_kb

        if not upload_dir.exists():
            return {"status": "error", "message": f"Upload folder not found for kb_id '{request.kb_id}'"}

        # Find all PDF files in the upload folder
        pdf_files = list(upload_dir.glob("*.pdf")) + list(upload_dir.glob("*.PDF"))
        if not pdf_files:
            return {"status": "error", "message": "No PDF files found in the upload folder"}

        logger.info(f"[/ingest] Found {len(pdf_files)} PDF(s) in {upload_dir}")

        # Step 1: Extract text from each PDF
        from src.preprocessing.preprocessing import DocumentProcessor
        doc_processor = DocumentProcessor()
        all_documents = []

        for pdf_path in pdf_files:
            pdf_path_str = str(pdf_path)
            logger.info(f"[/ingest] Processing: {pdf_path.name}")

            # Integrity check
            if not doc_processor.check_pdf_integrity(pdf_path_str):
                logger.warning(f"[/ingest] Skipping invalid PDF: {pdf_path.name}")
                continue

            # Primary extraction with pymupdf4llm
            documents = doc_processor.load_pdf_with_pymupdf4llm(pdf_path_str)

            # Fallback to pdfplumber
            if not documents or sum(len(d.page_content) for d in documents) < 100:
                logger.info(f"[/ingest] Low content from pymupdf4llm, falling back to pdfplumber...")
                documents = doc_processor.load_pdf_with_pdfplumber(pdf_path_str)

            if not documents:
                logger.warning(f"[/ingest] No content extracted from {pdf_path.name}")
                continue

            # Tag each document with the kb_id for potential future filtering
            for doc in documents:
                doc.metadata["kb_id"] = safe_kb

            all_documents.extend(documents)
            logger.info(f"[/ingest] Extracted {len(documents)} pages from {pdf_path.name}")

        if not all_documents:
            return {"status": "error", "message": "No content could be extracted from the uploaded PDFs"}

        # Step 2: Save Markdown artifacts to KB-specific subfolder
        markdown_root = Path(__file__).parent / "public" / "backend" / "markdowns"
        kb_markdown_dir = markdown_root / safe_kb
        kb_markdown_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[/ingest] Saving markdown artifacts to {kb_markdown_dir}...")
        doc_processor.generate_markdown_output(all_documents, output_folder=str(kb_markdown_dir))

        # Step 3: Ingest into Qdrant (chunk + embed + upsert)
        logger.info(f"[/ingest] Ingesting {len(all_documents)} pages into Qdrant...")
        initial_count = vector_store.client.count(collection_name=vector_store.collection_name).count
        await asyncio.to_thread(vector_store.add_documents, all_documents, batch_size=10)
        final_count = vector_store.client.count(collection_name=vector_store.collection_name).count
        chunks_created = final_count - initial_count

        logger.info(f"[/ingest] Ingestion complete. {chunks_created} new chunks added to Qdrant.")

        # Step 3: Rebuild both global and per-KB BM25 indexes
        if rag_connector:
            logger.info("[/ingest] Rebuilding global BM25 index...")
            await rag_connector.initialize_hybrid_retrieval()
            logger.info("[/ingest] Rebuilding per-KB BM25 index for '%s'...", safe_kb)
            await rag_connector.initialize_hybrid_retrieval(kb_id=safe_kb)
            logger.info("[/ingest] BM25 indexes rebuilt successfully.")

        # Step 4: Record per-file ingest status in docs_status.json
        from datetime import datetime, timezone
        docs_status = {}
        try:
            docs_status_path = upload_dir / "docs_status.json"
            if docs_status_path.exists():
                with docs_status_path.open("r", encoding="utf-8") as f:
                    docs_status = json.load(f)
        except Exception:
            pass

        chunks_per_file = chunks_created // max(len(pdf_files), 1)
        for pdf_path in pdf_files:
            docs_status[pdf_path.name] = {
                "status": "ingested",
                "chunks_created": chunks_per_file,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        with (upload_dir / "docs_status.json").open("w", encoding="utf-8") as f:
            json.dump(docs_status, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "kb_id": safe_kb,
            "files_ingested": len(pdf_files),
            "pages_extracted": len(all_documents),
            "chunks_created": chunks_created,
        }

    except Exception as e:
        logger.error(f"[/ingest] Error during ingestion: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


import json

CHAT_HISTORY_DIR = Path(__file__).parent / "public" / "chat_history"
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/save_chat")
async def save_chat(data: ChatSaveRequest):
    """Save an entire chat with messages to a JSON file in public/chat_history"""
    try:
        safe_id = _safe_name(data.conversation_id)
        if not safe_id:
            return {"status": "error", "message": "Invalid conversation ID"}
            
        file_path = CHAT_HISTORY_DIR / f"{safe_id}.json"
        
        chat_data = {
            "conversation_id": data.conversation_id,
            "meta": data.conversation_meta,
            "messages": data.messages
        }
        
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "file_path": str(file_path.relative_to(Path(__file__).parent))}
    except Exception as e:
        logger.error(f"Error saving chat: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ============================================================================
# KNOWLEDGE BASE MANAGEMENT ENDPOINTS
# ============================================================================

KB_META_FILE = "meta.json"
DOCS_STATUS_FILE = "docs_status.json"


def _read_kb_meta(kb_dir: Path) -> dict:
    """Read meta.json from a KB folder, returning defaults if missing."""
    meta_path = kb_dir / KB_META_FILE
    if meta_path.exists():
        try:
            with meta_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"name": kb_dir.name, "description": "", "created_at": ""}


def _write_kb_meta(kb_dir: Path, name: str, description: str, created_at: str) -> None:
    """Write meta.json to a KB folder."""
    meta = {"name": name, "description": description, "created_at": created_at}
    with (kb_dir / KB_META_FILE).open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def _read_docs_status(kb_dir: Path) -> dict:
    """Read docs_status.json from a KB folder."""
    status_path = kb_dir / DOCS_STATUS_FILE
    if status_path.exists():
        try:
            with status_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_docs_status(kb_dir: Path, status: dict) -> None:
    """Write docs_status.json to a KB folder."""
    with (kb_dir / DOCS_STATUS_FILE).open("w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)


@app.get("/list_kbs")
async def list_kbs():
    """
    List all knowledge bases currently stored on the server.
    Each KB is a subdirectory of UPLOAD_ROOT with an optional meta.json.
    """
    try:
        kbs = []
        for kb_dir in sorted(UPLOAD_ROOT.iterdir()):
            if not kb_dir.is_dir():
                continue
            meta = _read_kb_meta(kb_dir)
            # Count non-sidecar files
            doc_files = [
                f for f in kb_dir.iterdir()
                if f.is_file() and f.name not in (KB_META_FILE, DOCS_STATUS_FILE)
            ]
            kbs.append({
                "id": kb_dir.name,
                "name": meta.get("name", kb_dir.name),
                "description": meta.get("description", ""),
                "doc_count": len(doc_files),
                "created_at": meta.get("created_at", ""),
            })
        return {"status": "success", "knowledge_bases": kbs}
    except Exception as e:
        logger.error(f"[/list_kbs] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


class CreateKBRequest(BaseModel):
    """Request model for creating a new knowledge base."""
    id: str
    name: str
    description: str = ""


@app.post("/create_kb")
async def create_kb(request: CreateKBRequest):
    """Create a new knowledge base folder with metadata."""
    try:
        safe_id = _safe_name(request.id)
        kb_dir = UPLOAD_ROOT / safe_id

        if kb_dir.exists():
            # KB already exists — just update meta
            pass
        else:
            kb_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime, timezone
        created_at = datetime.now(timezone.utc).isoformat()
        _write_kb_meta(kb_dir, request.name.strip(), request.description.strip(), created_at)

        return {
            "status": "success",
            "id": safe_id,
            "name": request.name.strip(),
            "description": request.description.strip(),
            "created_at": created_at,
        }
    except Exception as e:
        logger.error(f"[/create_kb] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.delete("/delete_kb/{kb_id}")
async def delete_kb(kb_id: str):
    """
    Delete a knowledge base folder and all its files from disk.
    Note: vectors already pushed to Qdrant are NOT removed (global collection).
    """
    try:
        safe_id = _safe_name(kb_id)
        kb_dir = UPLOAD_ROOT / safe_id

        if not kb_dir.exists():
            return {"status": "error", "message": f"KB '{kb_id}' not found"}

        import shutil as _shutil
        # Delete PDF folder
        if kb_dir.exists():
            _shutil.rmtree(kb_dir)
            logger.info(f"[/delete_kb] Deleted KB PDF folder: {kb_dir}")

        # Delete Markdown folder
        markdown_root = Path(__file__).parent / "public" / "backend" / "markdowns"
        kb_md_dir = markdown_root / safe_id
        if kb_md_dir.exists():
            _shutil.rmtree(kb_md_dir)
            logger.info(f"[/delete_kb] Deleted KB Markdown folder: {kb_md_dir}")

        return {"status": "success", "message": f"KB '{safe_id}' deleted"}
    except Exception as e:
        logger.error(f"[/delete_kb] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/list_docs/{kb_id}")
async def list_docs(kb_id: str):
    """List all documents stored in a specific knowledge base folder."""
    try:
        safe_id = _safe_name(kb_id)
        kb_dir = UPLOAD_ROOT / safe_id

        if not kb_dir.exists():
            return {"status": "error", "message": f"KB '{kb_id}' not found"}

        docs_status = _read_docs_status(kb_dir)
        docs = []
        for f in sorted(kb_dir.iterdir()):
            if not f.is_file() or f.name in (KB_META_FILE, DOCS_STATUS_FILE):
                continue
            stat = f.stat()
            file_status = docs_status.get(f.name, {})
            docs.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "ingest_status": file_status.get("status", "uploaded"),
                "chunks_created": file_status.get("chunks_created", 0),
                "uploaded_at": file_status.get("uploaded_at", ""),
            })

        return {"status": "success", "kb_id": safe_id, "documents": docs}
    except Exception as e:
        logger.error(f"[/list_docs] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.delete("/delete_doc/{kb_id}/{filename}")
async def delete_doc(kb_id: str, filename: str):
    """Delete a single document from a knowledge base folder."""
    try:
        safe_id = _safe_name(kb_id)
        safe_file = _safe_name(filename)
        kb_dir = UPLOAD_ROOT / safe_id
        file_path = kb_dir / safe_file

        if not file_path.exists():
            return {"status": "error", "message": f"File '{safe_file}' not found in KB '{safe_id}'"}

        file_path.unlink()
        logger.info(f"[/delete_doc] Deleted PDF: {file_path}")

        # Also delete corresponding markdown file
        markdown_root = Path(__file__).parent / "public" / "backend" / "markdowns"
        md_path = markdown_root / safe_id / f"{os.path.splitext(safe_file)[0]}.md"
        if md_path.exists():
            md_path.unlink()
            logger.info(f"[/delete_doc] Deleted Markdown: {md_path}")

        # Remove from docs_status
        docs_status = _read_docs_status(kb_dir)
        docs_status.pop(safe_file, None)
        _write_docs_status(kb_dir, docs_status)

        return {"status": "success", "message": f"Document '{safe_file}' deleted"}
    except Exception as e:
        logger.error(f"[/delete_doc] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ============================================================================
# CHAT HISTORY READ ENDPOINTS
# ============================================================================

@app.get("/list_chats")
async def list_chats():
    """
    List all saved conversations (metadata only, not full messages).
    Reads each *.json file in CHAT_HISTORY_DIR and returns the meta block.
    """
    try:
        chats = []
        for chat_file in sorted(CHAT_HISTORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with chat_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("meta", {})
                messages = data.get("messages", [])
                # Build a lightweight preview
                last_user_msg = next(
                    (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
                )
                chats.append({
                    "id": data.get("conversation_id", chat_file.stem),
                    "title": meta.get("title", "Untitled"),
                    "preview": last_user_msg[:120],
                    "message_count": len(messages),
                    "kb_id": meta.get("kbId", ""),
                    "kb_name": meta.get("kbName", ""),
                    "updated_at": meta.get("updatedAt", ""),
                    "status": meta.get("status", "active"),
                })
            except Exception as parse_err:
                logger.warning(f"[/list_chats] Could not parse {chat_file.name}: {parse_err}")

        return {"status": "success", "conversations": chats}
    except Exception as e:
        logger.error(f"[/list_chats] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.get("/get_chat/{conversation_id}")
async def get_chat(conversation_id: str):
    """Retrieve the full message history for a specific conversation."""
    try:
        safe_id = _safe_name(conversation_id)
        chat_file = CHAT_HISTORY_DIR / f"{safe_id}.json"

        if not chat_file.exists():
            return {"status": "error", "message": f"Conversation '{conversation_id}' not found"}

        with chat_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return {"status": "success", **data}
    except Exception as e:
        logger.error(f"[/get_chat] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ============================================================================
# VIDORE EVALUATION ENDPOINT (ISOLATED FROM PRODUCTION)
# ============================================================================

class EvaluateViDoReRequest(BaseModel):
    """Request model for ViDoRe evaluation."""
    max_queries: int = 50
    k_values: list = [5, 10, 20]
    compare_strategies: bool = False
    use_reranker: bool = False
    use_hybrid: bool = False

@app.post("/evaluate_vidore")
async def evaluate_vidore(request: EvaluateViDoReRequest):
    """
    Evaluate RAG retrieval performance using ViDoRe V3 dataset.
    
    This endpoint is isolated and does NOT affect production RAG endpoints.
    
    Args:
        max_queries: Maximum number of queries to evaluate
        k_values: List of K values for Recall@K, Precision@K, NDCG@K
        compare_strategies: If True, compare different chunking strategies
        
    Returns:
        JSON with evaluation metrics
    """
    try:
        from src.evaluation.vidore_evaluator import ViDoReEvaluator
        from src.models.reranker_model import RerankerModel
        
        logger.info("Starting ViDoRe evaluation...")
        
        # Reuse existing Qdrant client from vector_store to avoid storage locking
        qdrant_client = vector_store.client if hasattr(vector_store, 'client') else None
        
        # Initialize reranker if requested
        reranker = None
        if request.use_reranker:
            logger.info("Initializing Cross-Encoder reranker...")
            reranker = RerankerModel()
        
        evaluator = ViDoReEvaluator(
            embedding_model=embedding_model,
            qdrant_client=qdrant_client,
            reranker=reranker,
            use_hybrid=request.use_hybrid
        )
        
        if request.compare_strategies:
            # Compare chunking strategies
            results = await evaluator.compare_chunking_strategies(
                k_values=request.k_values,
                max_queries=request.max_queries
            )
            return {
                "type": "strategy_comparison",
                "results": results,
                "visualization_data": evaluator.get_visualization_format(results)
            }
        else:
            # Standard evaluation
            results = await evaluator.evaluate_retrieval(
                k_values=request.k_values,
                max_queries=request.max_queries
            )
            return {
                "type": "standard_evaluation",
                **results
            }
            
    except Exception as e:
        logger.error(f"Error during ViDoRe evaluation: {e}", exc_info=True)
        return {
            "error": str(e),
            "message": "Evaluation failed. Check logs for details."
        }

@app.post("/ingest_vidore")
async def ingest_vidore_via_api():
    """
    Ingest ViDoRe dataset into Qdrant through the API.
    
    This avoids storage locking issues on Windows when uvicorn is running.
    """
    try:
        from src.evaluation.vidore_loader import ViDoReLoader
        from qdrant_client.models import Distance, VectorParams, PointStruct
        import uuid
        
        logger.info("Initializing ViDoRe ingestion via API...")
        loader = ViDoReLoader()
        
        # Load dataset
        logger.info("Loading ViDoRe dataset...")
        documents, queries = loader.download_and_process()
        
        if not documents:
            return {"status": "error", "message": "No documents found in dataset."}
            
        # Create collection
        collection_name = "vidore_eval"
        vector_size = getattr(embedding_model, 'dimension', 384)
        
        collections = vector_store.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if collection_name in collection_names:
            logger.info(f"Collection '{collection_name}' already exists. Recreating...")
            vector_store.client.delete_collection(collection_name)
        
        vector_store.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        
        # Ingest documents in batches
        from src.preprocessing.chunking_strategies import get_chunker
        
        # Use production settings from VectorStore
        chunk_size = 800
        chunk_overlap = 150
        
        chunker = get_chunker(
            'hierarchical',
            embedding_function=embedding_model,
            parent_size=1500,
            child_size=400
        )
        
        batch_size = 20
        total_docs = len(documents)
        total_chunks = 0
        
        for i in range(0, total_docs, batch_size):
            batch_docs = documents[i:i + batch_size]
            
            # Split texts into chunks using production strategy
            all_chunks_text = []
            all_chunks_meta = []
            
            for doc in batch_docs:
                # Use split_text from the chunker
                # HierarchicalChunker returns child chunks with parent metadata
                doc_chunks = chunker.split_text(doc["text"])
                for chunk in doc_chunks:
                    all_chunks_text.append(chunk.page_content)
                    # Merge chunk-specific metadata with document-level metadata
                    meta = chunk.metadata.copy()
                    if doc.get("metadata"):
                        meta.update(doc["metadata"])
                    meta["doc_id"] = doc["id"] # Ensure doc_id is preserved
                    all_chunks_meta.append(meta)
            
            if not all_chunks_text:
                continue
                
            # Generate embeddings for CHUNKS (not full pages)
            embeddings = await asyncio.to_thread(embedding_model.embed_documents, all_chunks_text)
            
            points = []
            for j, text in enumerate(all_chunks_text):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embeddings[j],
                    payload={
                        "text": text,
                        **all_chunks_meta[j]
                    }
                )
                points.append(point)
            
            vector_store.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            total_chunks += len(points)
            
            if (i + batch_size) % 100 == 0 or (i + batch_size) >= total_docs:
                logger.info(f"Processed {min(i + batch_size, total_docs)}/{total_docs} docs ({total_chunks} chunks)")
        
        return {
            "status": "success",
            "message": f"Ingested {len(documents)} documents and {len(queries)} queries.",
            "collection": collection_name,
            "queries_found": len(queries)
        }
        
    except Exception as e:
        logger.error(f"Error during ViDoRe ingestion: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/debug_vidore")
async def debug_vidore_internal():
    """
    Debug Qdrant state and retrieval logic internally.
    Checks collection count, retrieves a sample, and tests self-retrieval.
    """
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        import numpy as np
        
        results = {}
        collection_name = "vidore_eval"
        
        # 1. Check collection status
        try:
            count = vector_store.client.count(collection_name=collection_name).count
            results["total_vectors"] = count
        except Exception as e:
            return {"error": f"Collection check failed: {str(e)}"}

        if count == 0:
            return {"status": "error", "message": "Collection is empty"}

        # 2. Get a sample document
        try:
            scroll_result = vector_store.client.scroll(
                collection_name=collection_name,
                limit=1,
                with_payload=True,
                with_vectors=True
            )
            
            if not scroll_result[0]:
                return {"status": "error", "message": "No documents found via scroll"}
                
            point = scroll_result[0][0]
            sample_text = point.payload.get('text', '')
            sample_id = point.payload.get('doc_id')
            
            results["sample"] = {
                "id": point.id,
                "doc_id": sample_id,
                "text_preview": sample_text[:100],
                "vector_len": len(point.vector) if point.vector else 0,
                "vector_sample": point.vector[:5] if point.vector else []
            }
            
        except Exception as e:
            return {"error": f"Scroll failed: {str(e)}"}
            
        # 3. Test exact match retrieval
        try:
            # Embed the sample text
            query_vector = embedding_model.embed_query(sample_text)
            
            # Simple vector search
            search_result = vector_store.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=5,
                with_payload=True
            )
            
            hits = []
            for res in search_result.points:
                hits.append({
                    "score": res.score,
                    "doc_id": res.payload.get('doc_id'),
                    "match": str(res.payload.get('doc_id')) == str(sample_id)
                })
            
            results["self_retrieval_test"] = hits
            
            # Check if top hit matches
            if hits and hits[0]["match"]:
                results["sanity_check"] = "PASSED"
            else:
                results["sanity_check"] = "FAILED"
                
        except Exception as e:
            results["retrieval_error"] = str(e)
            
        return results
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app',host="0.0.0.0",  port=8000, reload=True)
