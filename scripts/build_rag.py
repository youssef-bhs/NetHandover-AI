#!/usr/bin/env python3
"""
Build RAG knowledge base from generic docs and project outputs.

Run this after adding new documents or updating the knowledge base.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.rag_service import rag_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Build knowledge base from scratch."""
    force_rebuild = "--rebuild" in sys.argv
    logger.info("Building RAG knowledge base...")
    if force_rebuild:
        logger.info("Rebuild requested: existing index will be replaced.")

    # Ensure directories exist
    settings.chroma_db_dir.mkdir(parents=True, exist_ok=True)
    settings.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    # Initialize RAG (build if empty or rebuild if requested)
    success = rag_service.initialize(force_rebuild=force_rebuild)
    if success:
        status = rag_service.get_status()
        logger.info(f"Knowledge base built: {status['document_count']} documents")
        logger.info(f"LLM model: {status.get('llm_model')}")
        logger.info("Done. You can now start the API server.")
    else:
        logger.error("Failed to build knowledge base")
        sys.exit(1)


if __name__ == "__main__":
    main()
