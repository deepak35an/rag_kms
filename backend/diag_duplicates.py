
import asyncio
import os
import sys
from pathlib import Path

src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from src.retrieval.rag_connector import RAGConnector
from src.retrieval.vector_store import VectorStore
from src.models.embedding_model import EmbeddingModel
from src.models.session_model import SessionManager

async def analyze_duplicates():
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)
    
    await rag_connector.initialize_hybrid_retrieval()
    
    question = "What are the participating institutes in JAC Chandigarh?"
    print(f"\nAnalyzing Hybrid Search for: '{question}'")
    
    results = await rag_connector.hybrid_similarity_search(question, k=10)
    
    print(f"\nResults Analysis:")
    print("-" * 50)
    for i, doc in enumerate(results):
        point_id = doc.metadata.get("id", "N/A")
        score = doc.metadata.get("relevance_score", 0.0)
        page = doc.metadata.get("page", "N/A")
        content_hash = hash(doc.page_content)
        print(f"[{i+1}] ID: {point_id} | Page: {page} | Score: {score:.4f} | Hash: {content_hash}")
    
    ids = [doc.metadata.get("id") for doc in results]
    unique_ids = set(ids)
    print(f"\nTotal Results: {len(results)}")
    print(f"Unique Point IDs: {len(unique_ids)}")
    if len(results) != len(unique_ids):
        print("!! WARNING: DUPLICATE POINT IDs DETECTED !!")
    else:
        print("✓ All Point IDs are unique.")

if __name__ == "__main__":
    asyncio.run(analyze_duplicates())
