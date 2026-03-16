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

@app.post("/ask")
async def ask_question(data: dict):
    """Process a question and return the response."""
    if generator is None:
        return {"error": "Generator not initialized. Server may still be starting up."}
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
