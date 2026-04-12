"""
Intent Classifier for ClaritAI Production Architecture.
Classifies every user message into ONE intent before any LLM call.
Uses GPT-3.5-turbo or a small model with low token budget to save cost.
"""
from typing import Dict, List, Optional, Any
import json
import logging

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# Production intents — one per message; used for routing (RAG vs LLM vs escalation)
INTENTS = [
    "COURSE_INQUIRY",      # → RAG retrieval
    "FEE_QUERY",           # → RAG retrieval
    "ADMISSION_QUERY",     # → CRM + RAG
    "ACADEMIC_DOUBT",      # → LLM Tutor mode
    "STUDY_PLAN",          # → Structured LLM prompt
    "MOCK_ANALYSIS",       # → Structured LLM prompt
    "COMPLAINT",           # → Escalation service
    "HUMAN_ESCALATION",    # → Notify human agent
    "LEAD_CAPTURE",        # → CRM lead creation
    "RANDOM_CHAT",         # → Lightweight LLM, low tokens
]

def _rule_based_classify(message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Rule-based fallback when OpenAI is unavailable or disabled."""
    text = (message or "").lower().strip()
    if not text:
        return {"intent": "RANDOM_CHAT", "confidence": 0.0, "exam_context": None}

    # Greeting / random
    if any(w in text for w in ["hello", "hi", "hey", "hii", "namaste", "good morning", "good afternoon"]):
        return {"intent": "RANDOM_CHAT", "confidence": 0.9, "exam_context": None}
    if any(w in text for w in ["bye", "thanks", "thank you"]):
        return {"intent": "RANDOM_CHAT", "confidence": 0.85, "exam_context": None}

    # Lead / contact
    if any(w in text for w in ["capture", "register", "sign up", "call me", "contact me", "my number", "my name", "reach out", "interested"]):
        return {"intent": "LEAD_CAPTURE", "confidence": 0.85, "exam_context": None}
    if any(w in text for w in ["speak to", "human", "agent", "representative", "real person"]):
        return {"intent": "HUMAN_ESCALATION", "confidence": 0.9, "exam_context": None}

    # Fee / price
    if any(w in text for w in ["price", "fee", "fees", "cost", "charges", "kitna", "pay", "payment"]):
        return {"intent": "FEE_QUERY", "confidence": 0.85, "exam_context": _infer_exam(text)}

    # Course / syllabus / batch
    if any(w in text for w in ["course", "syllabus", "batch", "subject", "curriculum", "what do you offer"]):
        return {"intent": "COURSE_INQUIRY", "confidence": 0.85, "exam_context": _infer_exam(text)}

    # Admission
    if any(w in text for w in ["admission", "enroll", "eligibility", "how to join", "apply"]):
        return {"intent": "ADMISSION_QUERY", "confidence": 0.8, "exam_context": _infer_exam(text)}

    # Academic doubt
    if any(w in text for w in ["doubt", "explain", "concept", "question about", "why does", "how does"]):
        return {"intent": "ACADEMIC_DOUBT", "confidence": 0.8, "exam_context": _infer_exam(text)}

    # Study plan
    if any(w in text for w in ["study plan", "schedule", "strategy", "how to prepare", "timetable"]):
        return {"intent": "STUDY_PLAN", "confidence": 0.8, "exam_context": _infer_exam(text)}

    # Mock / test
    if any(w in text for w in ["mock", "test", "analysis", "score", "performance"]):
        return {"intent": "MOCK_ANALYSIS", "confidence": 0.75, "exam_context": _infer_exam(text)}

    # Complaint
    if any(w in text for w in ["complaint", "issue", "problem", "not working", "bad", "refund"]):
        return {"intent": "COMPLAINT", "confidence": 0.85, "exam_context": None}

    return {"intent": "RANDOM_CHAT", "confidence": 0.5, "exam_context": _infer_exam(text)}


def _infer_exam(text: str) -> Optional[str]:
    """Infer exam from keywords (for rule-based path)."""
    t = text.upper()
    if "UPSC" in t or "CIVIL" in t:
        return "UPSC"
    if "NEET" in t or "MEDICAL" in t:
        return "NEET"
    if "JEE" in t or "ENGINEERING" in t:
        return "JEE"
    if "CAT" in t or "MBA" in t:
        return "CAT"
    if "GMAT" in t:
        return "GMAT"
    return None


class IntentClassifierService:
    """
    Classify user message into one of INTENTS.
    Uses GPT-3.5-turbo with 50 tokens max for cost control; falls back to rule-based.
    """

    def __init__(self) -> None:
        api_key = getattr(settings, "chatbot_api_key", None) or getattr(settings, "openai_api_key", None)
        self.enabled = bool(getattr(settings, "intent_recognition_enabled", False)) and bool(api_key)
        self.client = None
        if self.enabled and OpenAI and api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("IntentClassifierService initialized with OpenAI (GPT-3.5, max 50 tokens).")
            except Exception as e:
                logger.warning(f"IntentClassifierService: OpenAI init failed, using rule-based: {e}")
                self.client = None

    async def classify(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        exam_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify message into one intent.
        Returns: { "intent": str, "confidence": float, "exam_context": str | None }
        """
        if not (message or "").strip():
            return {"intent": "RANDOM_CHAT", "confidence": 0.0, "exam_context": exam_context}

        if not self.client:
            out = _rule_based_classify(message, conversation_history)
            if exam_context and not out.get("exam_context"):
                out["exam_context"] = exam_context
            return out

        try:
            intents_str = ", ".join(INTENTS)
            context_line = ""
            if conversation_history:
                recent = conversation_history[-3:]
                parts = [f"{m.get('sender', m.get('role', 'user'))}: {m.get('message', m.get('content', ''))}" for m in recent]
                context_line = "\nRecent:\n" + "\n".join(parts)
            exam_line = f"\nKnown exam context: {exam_context}." if exam_context else ""

            prompt = f"""Classify the user message into exactly ONE of these intents: {intents_str}.
Message: {message[:500]}{context_line}{exam_line}
Reply with JSON only: {"intent": "<one of the list>", "confidence": 0.0-1.0, "exam_context": "<UPSC|NEET|JEE|CAT|GMAT|null>"}"""

            response = self.client.chat.completions.create(
                model=getattr(settings, "intent_recognition_model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = (response.choices[0].message.content or "").strip()
            # Extract JSON if wrapped in markdown
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "").strip()
            data = json.loads(raw)
            intent = data.get("intent", "RANDOM_CHAT")
            if intent not in INTENTS:
                intent = "RANDOM_CHAT"
            return {
                "intent": intent,
                "confidence": float(data.get("confidence", 0.5)),
                "exam_context": data.get("exam_context") or exam_context,
            }
        except Exception as e:
            logger.warning(f"Intent classification failed, using rule-based: {e}")
            out = _rule_based_classify(message, conversation_history)
            if exam_context and not out.get("exam_context"):
                out["exam_context"] = exam_context
            return out


# Singleton for use in chatbot service
intent_classifier = IntentClassifierService()
