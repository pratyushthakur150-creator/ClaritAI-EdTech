"""
Intent recognition service for chatbot.
Detects user intent and extracts entities from messages.
"""
from typing import Dict, List, Optional
import json
import logging

try:
    import openai  # type: ignore
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - handled by env/config
    openai = None  # type: ignore
    OpenAI = None  # type: ignore

from app.core.config import settings


logger = logging.getLogger(__name__)


class IntentRecognitionService:
    """Service for detecting user intent from messages."""

    INTENTS = [
        "course_inquiry",      # Asking about courses
        "pricing_question",    # Asking about costs/pricing
        "demo_request",        # Wants to schedule a demo
        "enrollment_help",     # Help with enrollment process
        "support_request",     # Technical or general support
        "general_question",    # General information
        "greeting",            # Hello, hi, etc.
        "goodbye",             # Bye, thanks, etc.
        "other",               # Unclassified
    ]

    def __init__(self) -> None:
        """Initialize the intent recognition service."""
        self.enabled = bool(getattr(settings, "intent_recognition_enabled", False))

        api_key = getattr(settings, "chatbot_api_key", None) or getattr(
            settings, "openai_api_key", None
        )

        if self.enabled and OpenAI is not None and api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("IntentRecognitionService initialized with OpenAI client.")
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Failed to initialize OpenAI client for intent recognition: {e}")
                self.client = None
        else:
            self.client = None
            if not self.enabled:
                logger.info("IntentRecognitionService disabled via configuration.")
            else:
                logger.info("IntentRecognitionService running in rule-based fallback mode.")

    async def detect_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Detect user intent from message.

        Returns a dict:
            {
                "intent": "course_inquiry",
                "confidence": 0.95,
                "entities": {...}
            }
        """
        if not message:
            return {
                "intent": "other",
                "confidence": 0.0,
                "entities": {},
            }

        # Use rule-based fallback if client is not available
        if not self.enabled or not self.client:
            return self._rule_based_intent(message)

        try:
            context = ""
            if conversation_history:
                recent = conversation_history[-3:]
                parts = []
                for m in recent:
                    role = m.get("role") or m.get("sender") or "user"
                    content = m.get("content") or m.get("message") or ""
                    parts.append(f"{role}: {content}")
                context = "\n".join(parts)

            prompt = self._build_intent_prompt(message, context)

            response = self.client.chat.completions.create(
                model=getattr(settings, "intent_recognition_model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            if "intent" not in result:
                result["intent"] = "other"
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "entities" not in result:
                result["entities"] = {}

            return result

        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Intent recognition error, falling back to rule-based: {e}")
            return self._rule_based_intent(message)

    def _build_intent_prompt(self, message: str, context: str = "") -> str:
        """Build prompt for intent detection."""
        intents_str = ", ".join(self.INTENTS)

        context_block = f"\n\nRecent conversation:\n{context}\n" if context else ""

        prompt = f"""Analyze this message and detect the user's intent.

Available intents: {intents_str}

Message: {message}
{context_block}

Respond with JSON containing:
- intent: one of the available intents (string)
- confidence: confidence score 0-1 (number)
- entities: any important entities mentioned (object with key-value pairs)

Example entities:
- course_name: specific course mentioned
- urgency: low/medium/high
- budget: price range mentioned
- timeframe: when they want to start
- contact_preference: phone/email/chat

JSON response:
"""
        return prompt

    def _rule_based_intent(self, message: str) -> Dict:
        """Simple rule-based intent detection as fallback."""
        text = message.lower()

        # Greeting
        if any(w in text for w in ["hello", "hi ", " hi", "hey", "good morning", "good afternoon"]):
            return {"intent": "greeting", "confidence": 0.9, "entities": {}}

        # Goodbye / thanks
        if any(w in text for w in ["bye", "goodbye", "thanks", "thank you", "see you"]):
            return {"intent": "goodbye", "confidence": 0.9, "entities": {}}

        # Course inquiry
        if any(w in text for w in ["course", "program", "learn", "study", "teach"]):
            entities: Dict[str, str] = {}
            if "data science" in text:
                entities["course_name"] = "data science"
            elif "machine learning" in text or "ml" in text:
                entities["course_name"] = "machine learning"
            elif "python" in text:
                entities["course_name"] = "python"

            return {
                "intent": "course_inquiry",
                "confidence": 0.8,
                "entities": entities,
            }

        # Pricing
        if any(w in text for w in ["price", "cost", "fee", "payment", "afford", "expensive", "cheap"]):
            return {
                "intent": "pricing_question",
                "confidence": 0.85,
                "entities": {},
            }

        # Demo
        if any(w in text for w in ["demo", "trial", "preview", "show me", "try it"]):
            return {
                "intent": "demo_request",
                "confidence": 0.85,
                "entities": {},
            }

        # Enrollment
        if any(w in text for w in ["enroll", "register", "sign up", "join", "start"]):
            return {
                "intent": "enrollment_help",
                "confidence": 0.8,
                "entities": {},
            }

        # Support
        if any(w in text for w in ["help", "support", "problem", "issue", "error", "not working"]):
            return {
                "intent": "support_request",
                "confidence": 0.75,
                "entities": {},
            }

        # Default
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "entities": {},
        }

    def get_intent_metadata(self, intent: str) -> Dict:
        """Get metadata about an intent (for routing/handling)."""
        metadata = {
            "course_inquiry": {
                "requires_context": True,
                "can_escalate": False,
                "capture_lead": True,
                "priority": "high",
            },
            "pricing_question": {
                "requires_context": True,
                "can_escalate": False,
                "capture_lead": True,
                "priority": "high",
            },
            "demo_request": {
                "requires_context": False,
                "can_escalate": True,
                "capture_lead": True,
                "priority": "critical",
            },
            "enrollment_help": {
                "requires_context": True,
                "can_escalate": True,
                "capture_lead": True,
                "priority": "high",
            },
            "support_request": {
                "requires_context": False,
                "can_escalate": True,
                "capture_lead": False,
                "priority": "medium",
            },
            "general_question": {
                "requires_context": False,
                "can_escalate": False,
                "capture_lead": False,
                "priority": "low",
            },
            "greeting": {
                "requires_context": False,
                "can_escalate": False,
                "capture_lead": False,
                "priority": "low",
            },
            "goodbye": {
                "requires_context": False,
                "can_escalate": False,
                "capture_lead": False,
                "priority": "low",
            },
        }

        return metadata.get(
            intent,
            {
                "requires_context": False,
                "can_escalate": False,
                "capture_lead": False,
                "priority": "low",
            },
        )


# Global service instance
intent_service = IntentRecognitionService()

