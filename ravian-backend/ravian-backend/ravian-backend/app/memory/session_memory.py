"""
Session memory for chatbot: short-term in Redis, long-term in Postgres.
- Short-term: last 5 messages per session_id, TTL 30 minutes. Key: chat:{session_id}:history
- Long-term: use existing Postgres (Lead.exam_target, Lead.chatbot_context; ChatbotSession.conversation).
Never inject full history into prompt — only last 5 messages + user profile summary.
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Redis key pattern and limits
CHAT_KEY_PREFIX = "chat:"
CHAT_KEY_SUFFIX = ":history"
HISTORY_MAX_MESSAGES = 5
TTL_SECONDS = 30 * 60  # 30 minutes


def _get_redis():
    """Get Redis client (or None if unavailable)."""
    try:
        from app.core.redis_client import get_redis_client
        client = get_redis_client()
        if client and hasattr(client, "get") and hasattr(client, "setex"):
            return client
    except Exception as e:
        logger.debug(f"SessionMemory: Redis not available: {e}")
    return None


class SessionMemoryService:
    """
    Short-term: Redis store for last 5 messages per session.
    Long-term: Caller uses existing DB (Lead, ChatbotSession) for exam_target, weak_subjects, etc.
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client

    def _redis_key(self, session_id: str) -> str:
        return f"{CHAT_KEY_PREFIX}{session_id}{CHAT_KEY_SUFFIX}"

    def get_short_term_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get last up to HISTORY_MAX_MESSAGES messages for this session from Redis.
        Returns list of { sender, message } or { role, content }.
        """
        redis_client = self._redis or _get_redis()
        if not redis_client:
            return []
        try:
            key = self._redis_key(session_id)
            raw = redis_client.get(key)
            if not raw:
                return []
            data = json.loads(raw) if isinstance(raw, str) else raw
            messages = data.get("messages", [])
            return messages[-HISTORY_MAX_MESSAGES:] if messages else []
        except Exception as e:
            logger.debug(f"SessionMemory get_short_term_history: {e}")
            return []

    def append_short_term(
        self,
        session_id: str,
        sender: str,
        message: str,
        existing_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Append one message and keep only last HISTORY_MAX_MESSAGES. Store in Redis with TTL.
        If existing_messages is provided, use them as current history before appending.
        Returns the updated list (last 5) for caller to use.
        """
        redis_client = self._redis or _get_redis()
        messages = list(existing_messages) if existing_messages else self.get_short_term_history(session_id)
        messages.append({"sender": sender, "message": message})
        messages = messages[-HISTORY_MAX_MESSAGES:]
        if redis_client:
            try:
                key = self._redis_key(session_id)
                redis_client.setex(
                    key,
                    TTL_SECONDS,
                    json.dumps({"messages": messages}),
                )
            except Exception as e:
                logger.debug(f"SessionMemory append_short_term: {e}")
        return messages

    def get_user_profile_summary(
        self,
        exam_target: Optional[str] = None,
        preparation_stage: Optional[str] = None,
        lead_stage: Optional[str] = None,
    ) -> str:
        """
        Build a one-line user profile summary for prompt injection (long-term data from Postgres).
        Caller passes in data from Lead or ChatbotSession.
        """
        parts = []
        if exam_target:
            parts.append(f"Exam target: {exam_target}")
        if preparation_stage:
            parts.append(f"Stage: {preparation_stage}")
        if lead_stage:
            parts.append(f"Lead stage: {lead_stage}")
        if not parts:
            return ""
        return "User profile: " + ". ".join(parts)


# Optional singleton for dependency injection
_session_memory: Optional[SessionMemoryService] = None


def get_session_memory(redis_client=None) -> SessionMemoryService:
    """Get SessionMemoryService instance (singleton or new with optional redis_client)."""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemoryService(redis_client=redis_client)
    return _session_memory
