"""
Reset and Re-ingest Script for RAG4GOV

Deletes the existing Qdrant vector store and re-ingests all PDFs
from the ./public folder using the current chunking strategy (hierarchical).

Usage:
    python reset_and_reingest.py

WARNING: This will permanently delete all existing vectors in qdrant_storage/.
         Make sure the server (uvicorn) is NOT running before executing this.
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# ── environment fixes (must be before any torch/onnx imports) ──────────────
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# ── path setup ─────────────────────────────────────────────────────────────
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# ── logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

QDRANT_STORAGE = Path(__file__).parent / "qdrant_storage"


def delete_qdrant_storage() -> bool:
    """Delete the Qdrant storage directory."""
    if not QDRANT_STORAGE.exists():
        logger.info(f"qdrant_storage does not exist — nothing to delete.")
        return True

    logger.info(f"Deleting {QDRANT_STORAGE} ...")
    try:
        shutil.rmtree(QDRANT_STORAGE)
        logger.info("✓ qdrant_storage deleted.")
        return True
    except PermissionError:
        logger.error(
            "✗ Could not delete qdrant_storage — it may be locked by a running "
            "uvicorn/FastAPI server. Stop the server first and try again."
        )
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error while deleting qdrant_storage: {e}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("  RAG4GOV — Reset & Re-ingest")
    logger.info("=" * 60)

    # Step 1: Delete old storage
    logger.info("\nStep 1: Clearing existing Qdrant storage...")
    if not delete_qdrant_storage():
        sys.exit(1)

    # Step 2: Run ingestion
    logger.info("\nStep 2: Starting document ingestion...")
    try:
        from ingest_documents import ingest_pdf_from_public_folder
        success = ingest_pdf_from_public_folder()
    except Exception as e:
        logger.error(f"✗ Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

    if success:
        logger.info("\n✓ Reset and re-ingestion completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n✗ Ingestion failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
