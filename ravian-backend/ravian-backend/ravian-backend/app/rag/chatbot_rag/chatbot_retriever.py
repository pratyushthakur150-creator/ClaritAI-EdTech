"""
Chatbot Retriever — Query ChromaDB for relevant exam knowledge chunks.

Mirrors the retrieval pattern from TeachingAssistantService.search_course_context()
but optimized for the chatbot (faster, fewer chunks, cross-exam support).
"""
import os
import logging
from typing import Dict, List, Optional

import chromadb

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"

# Map user-facing exam names to collection suffixes
_EXAM_ALIASES = {
    "UPSC": "upsc",
    "JEE": "jee",
    "JEE Main": "jee",
    "JEE Advanced": "jee",
    "NEET": "neet",
    "CAT": "cat_mba",
    "CAT/MBA": "cat_mba",
    "MBA": "cat_mba",
    "GMAT": "gmat",
}

ALL_EXAMS = ["upsc", "jee", "neet", "cat_mba", "gmat"]


def _get_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        return None
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
        return None
    return OpenAI(api_key=api_key)


def _get_chroma_client() -> chromadb.ClientAPI:
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=chroma_path)


def _normalize_exam(exam_target: Optional[str]) -> Optional[str]:
    """Normalize user-facing exam name to collection suffix."""
    if not exam_target:
        return None
    exam_upper = exam_target.strip().upper()
    # Direct lookup
    for alias, normalized in _EXAM_ALIASES.items():
        if alias.upper() == exam_upper:
            return normalized
    # Partial match
    for alias, normalized in _EXAM_ALIASES.items():
        if alias.upper() in exam_upper or exam_upper in alias.upper():
            return normalized
    return None


def _embed_query(query: str, openai_client) -> List[float]:
    """Generate embedding for a query string."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    return response.data[0].embedding


async def retrieve_exam_context(
    query: str,
    exam_target: Optional[str] = None,
    top_k: int = 3,
    min_relevance: float = 0.3,
) -> List[Dict]:
    """
    Retrieve relevant exam knowledge chunks from ChromaDB.

    Args:
        query: The user's message/question
        exam_target: e.g. "UPSC", "JEE", "NEET", "CAT", "GMAT"
        top_k: Maximum chunks to retrieve (default 3)
        min_relevance: Minimum relevance score (1 - distance) to include

    Returns:
        List of {"text": str, "relevance": float, "exam": str}
    """
    try:
        normalized = _normalize_exam(exam_target)
        if normalized:
            return await _retrieve_from_collection(query, normalized, top_k, min_relevance)
        else:
            # No specific exam — search across all
            return await retrieve_cross_exam_context(query, top_k=top_k)
    except Exception as e:
        logger.warning(f"RAG retrieval failed (graceful fallback): {e}")
        return []


async def _retrieve_from_collection(
    query: str,
    exam_name: str,
    top_k: int,
    min_relevance: float,
) -> List[Dict]:
    """Query a specific exam collection in ChromaDB."""
    openai_client = _get_openai_client()
    if not openai_client:
        logger.warning("OpenAI client not available for RAG retrieval")
        return []

    client = _get_chroma_client()
    col_name = f"chatbot_exam_{exam_name}"

    try:
        collection = client.get_collection(name=col_name)
    except Exception:
        # Collection doesn't exist — try loading it
        logger.info(f"Collection '{col_name}' not found, attempting to load...")
        try:
            from app.rag.chatbot_rag.exam_knowledge_loader import load_exam_document
            await load_exam_document(exam_name)
            collection = client.get_collection(name=col_name)
        except Exception as load_err:
            logger.warning(f"Failed to auto-load exam '{exam_name}': {load_err}")
            return []

    count = collection.count()
    if count == 0:
        return []

    query_embedding = _embed_query(query, openai_client)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if results.get("documents") and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results.get("distances", [[0] * len(results["documents"][0])])[0],
        ):
            relevance = 1 - float(dist) if dist else 1.0
            if relevance >= min_relevance:
                chunks.append({
                    "text": doc,
                    "relevance": relevance,
                    "exam": meta.get("exam", exam_name),
                })

    logger.info(
        f"RAG retrieved {len(chunks)} chunks from '{col_name}' "
        f"(top_k={top_k}, min_rel={min_relevance})"
    )
    return chunks


async def retrieve_cross_exam_context(
    query: str,
    top_k: int = 2,
) -> List[Dict]:
    """
    Search across ALL exam collections for queries without a specific target.

    Used when exam_target is None or unrecognized.
    """
    try:
        openai_client = _get_openai_client()
        if not openai_client:
            return []

        client = _get_chroma_client()
        query_embedding = _embed_query(query, openai_client)

        all_chunks = []
        for exam_name in ALL_EXAMS:
            col_name = f"chatbot_exam_{exam_name}"
            try:
                collection = client.get_collection(name=col_name)
                count = collection.count()
                if count == 0:
                    continue

                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(1, count),  # 1 per collection for cross-exam
                    include=["documents", "metadatas", "distances"]
                )

                if results.get("documents") and results["documents"][0]:
                    for doc, meta, dist in zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results.get("distances", [[0]])[0] if results.get("distances") else [0],
                    ):
                        relevance = 1 - float(dist) if dist else 1.0
                        if relevance >= 0.3:
                            all_chunks.append({
                                "text": doc,
                                "relevance": relevance,
                                "exam": meta.get("exam", exam_name),
                            })
            except Exception:
                continue  # Skip unavailable collections

        # Sort by relevance and return top_k
        all_chunks.sort(key=lambda c: c["relevance"], reverse=True)
        return all_chunks[:top_k]

    except Exception as e:
        logger.warning(f"Cross-exam RAG retrieval failed: {e}")
        return []
