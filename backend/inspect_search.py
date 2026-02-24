
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

async def inspect_search():
    # 1. Init components
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model.embeddings)
    session_manager = SessionManager()
    rag_connector = RAGConnector(vector_store, session_manager)
    
    # 2. Build BM25 index
    await rag_connector.initialize_hybrid_retrieval()
    
    # 3. Query
    question = "Tell me about Fee, Refund rules and total intake of  Chandigarh College of Engineering and Technology"
    print(f"\nRunning search for: '{question}'")
    
    results = await rag_connector.hybrid_similarity_search(question, k=10)
    
    # 4. Save to Markdown
    output_path = r"c:\Users\Asus tuf\OneDrive\Desktop\New folder\LaFleur_Tech\rag4gov\search_inspection.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Search Inspection Results\n\n")
        f.write(f"**Query:** {question}\n\n")
        f.write(f"**Total Results Found:** {len(results)}\n\n---\n\n")
        
        for i, doc in enumerate(results):
            score = doc.metadata.get("relevance_score", 0.0)
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            point_id = doc.metadata.get("id", "N/A")
            
            f.write(f"## [{i+1}] Result Info\n")
            f.write(f"- **Score:** {score:.4f}\n")
            f.write(f"- **Source:** {source}\n")
            f.write(f"- **Page:** {page}\n")
            f.write(f"- **Point ID:** `{point_id}`\n\n")
            f.write(f"### Metadata\n```json\n{doc.metadata}\n```\n\n")
            f.write(f"### Full Content\n\n{doc.page_content}\n\n")
            f.write(f"---\n\n")
            
    print(f"\n✓ Saved full results to: {os.path.abspath(output_path)}")
    print("You can now open this file in your editor to see the full chunk data.")

if __name__ == "__main__":
    asyncio.run(inspect_search())
