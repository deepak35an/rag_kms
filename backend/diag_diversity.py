
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

async def analyze_bottleneck():
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)
    await rag_connector.initialize_hybrid_retrieval()
    
    question = "what steps are involved in round 1 of councelling ?"
    print(f"\n--- ANALYZING RETRIEVAL for: '{question}' ---")
    
    # 1. Raw Retrieval
    dense_docs = await vector_store.similarity_search(question, k=25)
    
    # Let's count how many UNIQUE content chunks are in the top 25 DENSE
    seen_norm = set()
    unique_dense = 0
    for d in dense_docs:
        norm = " ".join(d.page_content.lower().split())
        if norm not in seen_norm:
            unique_dense += 1
            seen_norm.add(norm)
            
    print(f"Top 25 Dense Results:")
    print(f" - Total: 25")
    print(f" - Unique Content Chunks: {unique_dense}")
    
    # 2. Hybrid Results
    results = await rag_connector.hybrid_similarity_search(question, k=10)
    print(f"\nFinal Hybrid Results (after Fusion, Rerank, Dedup): {len(results)}")
    
    if len(results) < 5:
        print("\n!! WARNING: Diversity is low !!")
        print("This usually means:")
        print("1. Your database has many identical 'clones' of the same few chunks.")
        print("2. The query is very specific and only matches one part of the document.")
        
    print("\n--- CONTENT PREVIEW (Top Results) ---")
    for i, doc in enumerate(results):
        print(f"Result {i+1} (Page {doc.metadata.get('page')}): {doc.page_content[:100]}...")

if __name__ == "__main__":
    asyncio.run(analyze_bottleneck())
