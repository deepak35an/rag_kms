"""
PDF Ingestion Script for Qdrant Vector Store

This script processes PDF documents from the public folder and ingests them
into the Qdrant vector database for RAG retrieval.

Usage:
    python ingest_documents.py
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# FIX for OpenMP crash
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import logging
from src.models.embedding_model import EmbeddingModel
from src.retrieval.vector_store import VectorStore
from src.preprocessing.preprocessing import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ingest_pdf_from_public_folder():
    """Ingest PDF documents from the public folder into Qdrant."""
    
    logger.info("="* 60)
    logger.info("Starting PDF Ingestion Process")
    logger.info("="* 60)
    
    # Step 1: Initialize components
    logger.info("Step 1: Initializing components...")
    try:
        embedding_model = EmbeddingModel()
        logger.info("✓ Embedding model initialized")
        
        vector_store = VectorStore(embedding_model.embeddings)
        logger.info("✓ Vector store initialized")
        
        doc_processor = DocumentProcessor()
        logger.info("✓ Document processor initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize components: {e}")
        return False
    
    # Step 2: Find PDF files in public folder
    pdf_folder = "./public"
    logger.info(f"\nStep 2: Looking for PDFs in '{pdf_folder}'...")
    
    if not os.path.exists(pdf_folder):
        logger.error(f"✗ Public folder not found: {pdf_folder}")
        return False
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"✗ No PDF files found in {pdf_folder}")
        return False
    
    logger.info(f"✓ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        logger.info(f"  - {pdf}")
    
    # Step 3: Process each PDF
    all_documents = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        logger.info(f"\nStep 3: Processing '{pdf_file}'...")
        
        try:
            # Check PDF integrity
            if not doc_processor.check_pdf_integrity(pdf_path):
                logger.error(f"✗ PDF integrity check failed for {pdf_file}")
                continue
            
            logger.info(f"✓ PDF integrity verified")
            
            # Extract content from PDF using PyMuPDF4LLM (Markdown support)
            logger.info(f"  Extracting content with PyMuPDF4LLM...")
            documents = doc_processor.load_pdf_with_pymupdf4llm(pdf_path)
            
            # Fallback if needed
            if not documents or sum(len(d.page_content) for d in documents) < 100:
                logger.info(f"  Low content with PyMuPDF, falling back to pdfplumber...")
                documents = doc_processor.load_pdf_with_pdfplumber(pdf_path)
            
            if not documents:
                logger.warning(f"✗ No content extracted from {pdf_file}")
                continue
            
            logger.info(f"✓ Extracted {len(documents)} page(s)")
            
            # Add to collection
            all_documents.extend(documents)
            
        except Exception as e:
            logger.error(f"✗ Error processing {pdf_file}: {e}", exc_info=True)
            continue
    
    if not all_documents:
        logger.error("\n✗ No documents were successfully processed")
        return False
    
    logger.info(f"\n✓ Total documents extracted: {len(all_documents)}")
    
    # Save to Markdown folder for inspection
    logger.info("\nStep 3.5: Saving extracted content to markdowns folder...")
    doc_processor.generate_markdown_output(all_documents, output_folder="./markdowns")
    logger.info("✓ Markdown files generated in ./markdowns/")
    
    # Step 4: Ingest into Qdrant
    logger.info(f"\nStep 4: Ingesting documents into Qdrant...")
    
    try:
        vector_store.add_documents(all_documents, batch_size=10)
        logger.info("✓ Documents successfully ingested into Qdrant!")
        
    except Exception as e:
        logger.error(f"✗ Failed to ingest documents: {e}", exc_info=True)
        return False
    
    # Step 5: Verify ingestion
    logger.info(f"\nStep 5: Verifying ingestion...")
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(path="./qdrant_storage")
        count = client.count(collection_name="rag4gov_documents").count
        logger.info(f"✓ Qdrant collection now contains {count} vectors")
        
    except Exception as e:
        logger.warning(f"! Could not verify count: {e}")
    
    logger.info("\n" + "="* 60)
    logger.info("✓ INGESTION COMPLETE!")
    logger.info("="* 60)
    logger.info("\nYou can now query your documents using:")
    logger.info("  - /test_simple endpoint")
    logger.info("  - /test_rag endpoint")
    logger.info("  - /ask endpoint")
    
    return True

def main():
    """Main entry point."""
    try:
        success = ingest_pdf_from_public_folder()
        if success:
            logger.info("\n✓ Process completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n✗ Process failed. Check logs above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n\n! Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
