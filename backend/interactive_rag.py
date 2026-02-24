
"""
Interactive RAG CLI for "through and fro" question answering.

Usage:
  1. Ensure Ollama is running.
  2. Run: python interactive_rag.py
  3. Type your questions. Type 'exit' to quit.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
# Suppress heavy logging for a cleaner CLI experience
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("interactive_rag")
logger.setLevel(logging.INFO)

from src.retrieval.rag_connector import RAGConnector
from src.retrieval.vector_store import VectorStore
from src.models.embedding_model import EmbeddingModel
from src.models.session_model import SessionManager

async def interactive_loop():
    print("\n" + "="*60)
    print("🤖 INTERACTIVE RAG CHATBOT")
    print("="*60)
    print("Initializing components... Please wait.")

    # 1. Initialize Components
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)

    if not rag_connector.llm:
        print("\n❌ Error: Local LLM (Ollama) not initialized.")
        print("   Ensure Ollama is running and Llama 3.2 3B is pulled.")
        return

    # 2. Build BM25 Index
    print("Building BM25 index from knowledge base...")
    await rag_connector.initialize_hybrid_retrieval()
    
    print("\n✅ System Ready! Ask me anything about the documents.")
    print("   (Type 'exit' or 'quit' to stop, 'clear' to reset terminal)\n")

    # 3. Chat Loop
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nAssistant: Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\n✅ Terminal cleared. Ask me anything!\n")
                continue

            if not user_input:
                continue

            print("\n🤖 Thinking...", end="\r")
            
            # Run the RAG pipeline
            result = await rag_connector.generate_answer(user_input, k=10)
            
            print(" " * 20, end="\r") # Clear the thinking line
            print(f"🤖 Assistant:\n{result['answer']}")
            
            if result.get('sources'):
                source_strings = {f"{s['source']} (p.{s['page']})" for s in result['sources']}
                print(f"\n📄 Sources: {', '.join(source_strings)}")
            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\nAssistant: Session interrupted. Goodbye! ")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("-" * 60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(interactive_loop())
    except Exception as e:
        print(f"Fatal error: {e}")
