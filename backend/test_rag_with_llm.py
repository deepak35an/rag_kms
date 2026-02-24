
"""
End-to-end test of Hybrid Retrieval + Ollama LLM Answer Generation.

Before running:
  1. Install Ollama from https://ollama.com/download
  2. Run: ollama pull llama3.2:1b-instruct-q4_K_M
  3. Make sure Ollama is running (it starts by default after install)
  4. Then: python test_rag_with_llm.py
"""
import asyncio
import os
import sys
from pathlib import Path

src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
logging.basicConfig(level=logging.INFO)

from src.retrieval.rag_connector import RAGConnector
from src.retrieval.vector_store import VectorStore
from src.models.embedding_model import EmbeddingModel
from src.models.session_model import SessionManager

async def test_rag():
    print("\n" + "="*60)
    print("END-TO-END RAG TEST (Hybrid Retrieval + LLM)")
    print("="*60)

    # 1. Init
    print("\n[1/3] Initializing components...")
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)

    if not rag_connector.llm:
        print("\n❌ LLM is not initialized!")
        print("   Please install Ollama from https://ollama.com/download")
        print("   Then run: ollama pull llama3.2:1b-instruct-q4_K_M")
        return

    print(f"   ✓ LLM ready: {type(rag_connector.llm).__name__}")

    # 2. Build BM25 index
    print("\n[2/3] Building BM25 index from Qdrant...")
    await rag_connector.initialize_hybrid_retrieval()

    if not rag_connector.bm25_retriever:
        print("   ❌ BM25 retriever not initialized. Re-ingest documents first.")
        return

    # 3. Full RAG Q&A
    question = "Explain all counselling rounds in detail."
    print(f"\n[3/3] Running full RAG pipeline for: '{question}'")
    print("-" * 60)

    result = await rag_connector.generate_answer(question, k=10)

    print(f"\n🤖 ANSWER:\n{result['answer']}")
    print(f"\n📄 SOURCES ({len(result['sources'])}):")
    for s in result['sources']:
        print(f"   - {s['source']} (Page {s['page']})")
    print(f"\n📦 CHUNKS USED: {len(result['retrieved_chunks'])}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_rag())
