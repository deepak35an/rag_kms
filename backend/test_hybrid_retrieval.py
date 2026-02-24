
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Fix OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
from src.retrieval.rag_connector import RAGConnector
from src.retrieval.vector_store import VectorStore
from src.models.embedding_model import EmbeddingModel
from src.models.session_model import SessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hybrid():
    print("\n" + "="*50)
    print("HYBRID RETRIEVAL VERIFICATION")
    print("="*50)
    
    # 1. Init components
    print("\n1. Initializing components...")
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)
    
    # 2. Build BM25 index
    print("\n2. Building BM25 index from Qdrant scroll...")
    await rag_connector.initialize_hybrid_retrieval()
    
    if not rag_connector.bm25_retriever:
        print("ERROR: BM25 retriever not initialized!")
        return

    # 3. Execute Hybrid Search
    question = "what steps are involved in round 1 of councelling ?"
    print(f"\n3. Executing Hybrid Search for: '{question}'")
    
    results = await rag_connector.hybrid_similarity_search(question, k=10)
    
    print(f"\n4. Final Top {len(results)} Results:")
    print("-" * 30)
    for i, doc in enumerate(results):
        score = doc.metadata.get("relevance_score", "N/A")
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "N/A")
        print(f"[{i+1}] Score: {score:.4f} | {source} (Page {page})")
        print(f"    Content: {doc.page_content[:150]}...")
        print("-" * 30)

    print("\n✓ Hybrid Retrieval Verification Complete!")

if __name__ == "__main__":
    asyncio.run(test_hybrid())
