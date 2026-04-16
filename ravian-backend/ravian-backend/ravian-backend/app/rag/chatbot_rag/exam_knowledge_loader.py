"""
Exam Knowledge Loader — Load exam documents into ChromaDB for chatbot RAG.

Uses the SAME embedding model (text-embedding-3-small) and ChromaDB client
pattern as the Teaching Assistant's content_indexing_service.py.

Collection naming: chatbot_exam_{exam_name}
  e.g. chatbot_exam_upsc, chatbot_exam_jee, chatbot_exam_neet
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

import chromadb

logger = logging.getLogger(__name__)

# Must match Teaching Assistant embedding model
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500       # characters — smaller than TA's 800 for faster retrieval
CHUNK_OVERLAP = 50     # characters overlap between chunks
DOCUMENTS_DIR = Path(__file__).resolve().parent / "documents"

# All supported exams and their document filenames
EXAM_DOCUMENTS = {
    "upsc": "upsc_knowledge.txt",
    "jee": "jee_knowledge.txt",
    "neet": "neet_knowledge.txt",
    "cat_mba": "cat_mba_knowledge.txt",
    "gmat": "gmat_knowledge.txt",
    "sssi": "sssi_knowledge.txt",  # SSSi Online Tutoring pilot tenant
}


def _get_openai_client():
    """Get OpenAI client using same key as the rest of the app."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed")
    # Use settings (loaded from .env) — os.getenv won't work if key is only in .env
    try:
        from app.core.config import settings as _settings
        api_key = getattr(_settings, "chatbot_api_key", None) or getattr(_settings, "openai_api_key", None)
    except Exception:
        api_key = None
    # Fallback to env var
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CHATBOT_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY or CHATBOT_API_KEY not set")
    return OpenAI(api_key=api_key)


def _get_chroma_client() -> chromadb.ClientAPI:
    """Get a ChromaDB persistent client using the same path as the app."""
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=chroma_path)


def _collection_name(exam_name: str) -> str:
    """Convert exam name to ChromaDB collection name."""
    return f"chatbot_exam_{exam_name.lower().replace('/', '_').replace(' ', '_')}"


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    # Split by section headers first for better semantic boundaries
    sections = text.split("\n\n")
    current_chunk = ""

    for section in sections:
        if not section.strip():
            continue
        # If adding this section would exceed chunk size, save current and start new
        if len(current_chunk) + len(section) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap from end of previous chunk
            if len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + section
            else:
                current_chunk = section
        else:
            current_chunk = current_chunk + "\n\n" + section if current_chunk else section

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # If any chunk is still too large, split by lines
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size * 1.5:  # allow 50% buffer
            final_chunks.append(chunk)
        else:
            lines = chunk.split("\n")
            sub_chunk = ""
            for line in lines:
                if len(sub_chunk) + len(line) > chunk_size and sub_chunk:
                    final_chunks.append(sub_chunk.strip())
                    sub_chunk = line
                else:
                    sub_chunk = sub_chunk + "\n" + line if sub_chunk else line
            if sub_chunk.strip():
                final_chunks.append(sub_chunk.strip())

    return [c for c in final_chunks if c.strip()]


def _get_embeddings(texts: List[str], openai_client) -> List[List[float]]:
    """Generate embeddings using same model as Teaching Assistant."""
    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


async def is_exam_indexed(exam_name: str) -> bool:
    """Check if exam knowledge already exists in ChromaDB."""
    try:
        client = _get_chroma_client()
        col_name = _collection_name(exam_name)
        try:
            collection = client.get_collection(name=col_name)
            return collection.count() > 0
        except Exception:
            return False
    except Exception as e:
        logger.warning(f"Failed to check if {exam_name} is indexed: {e}")
        return False


async def load_exam_document(exam_name: str, force_reload: bool = False) -> bool:
    """
    Load a single exam document into ChromaDB.

    Args:
        exam_name: One of 'upsc', 'jee', 'neet', 'cat_mba', 'gmat'
        force_reload: If True, delete existing collection and re-index

    Returns:
        True if loaded successfully, False otherwise
    """
    try:
        filename = EXAM_DOCUMENTS.get(exam_name)
        if not filename:
            logger.error(f"Unknown exam: {exam_name}")
            return False

        doc_path = DOCUMENTS_DIR / filename
        if not doc_path.exists():
            logger.error(f"Document not found: {doc_path}")
            return False

        col_name = _collection_name(exam_name)
        client = _get_chroma_client()

        # Check if already indexed (skip re-indexing unless forced)
        if not force_reload:
            try:
                collection = client.get_collection(name=col_name)
                if collection.count() > 0:
                    logger.info(f"Exam '{exam_name}' already indexed ({collection.count()} chunks) — skipping")
                    return True
            except Exception:
                pass  # Collection doesn't exist yet, proceed

        # If force reload, delete existing collection
        if force_reload:
            try:
                client.delete_collection(name=col_name)
                logger.info(f"Deleted existing collection: {col_name}")
            except Exception:
                pass  # Collection didn't exist

        # Read document
        text = doc_path.read_text(encoding="utf-8")
        logger.info(f"Read {len(text)} chars from {doc_path.name}")

        # Chunk
        chunks = _chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks from {doc_path.name}")

        if not chunks:
            logger.warning(f"No chunks created from {doc_path.name}")
            return False

        # Generate embeddings
        openai_client = _get_openai_client()
        embeddings = _get_embeddings(chunks, openai_client)
        logger.info(f"Generated {len(embeddings)} embeddings for {exam_name}")

        # Store in ChromaDB
        collection = client.get_or_create_collection(
            name=col_name,
            metadata={"exam": exam_name, "type": "chatbot_exam_knowledge"}
        )

        ids = [f"{exam_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"exam": exam_name, "chunk_index": i, "source": filename}
            for i in range(len(chunks))
        ]

        # Add in batches of 500 (ChromaDB limit)
        for i in range(0, len(ids), 500):
            collection.add(
                ids=ids[i:i + 500],
                embeddings=embeddings[i:i + 500],
                documents=chunks[i:i + 500],
                metadatas=metadatas[i:i + 500],
            )

        logger.info(f"✓ Loaded {len(chunks)} chunks for '{exam_name}' into ChromaDB collection '{col_name}'")
        return True

    except Exception as e:
        logger.error(f"Failed to load exam document '{exam_name}': {e}")
        return False


async def load_all_exams(force_reload: bool = False) -> Dict[str, bool]:
    """
    Load all 5 exam documents into ChromaDB.

    Returns:
        Dict like {"upsc": True, "jee": True, "neet": True, "cat_mba": True, "gmat": True}
    """
    results = {}
    for exam_name in EXAM_DOCUMENTS:
        results[exam_name] = await load_exam_document(exam_name, force_reload=force_reload)
    return results
