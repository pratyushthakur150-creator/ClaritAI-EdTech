"""
Context Builder — Convert retrieved RAG chunks into clean prompt context
for the Aria chatbot system prompt.

Includes cross-exam detection for graceful exam switches.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# All recognized exam names mapped to their canonical form
_EXAM_KEYWORDS = {
    "upsc": "UPSC",
    "ias": "UPSC",
    "ips": "UPSC",
    "civil services": "UPSC",
    "jee": "JEE",
    "jee main": "JEE",
    "jee advanced": "JEE",
    "iit": "JEE",
    "nit": "JEE",
    "neet": "NEET",
    "mbbs": "NEET",
    "medical": "NEET",
    "cat": "CAT",
    "cat/mba": "CAT",
    "mba": "CAT",
    "iim": "CAT",
    "gmat": "GMAT",
    "b-school": "GMAT",
}


def detect_cross_exam_query(
    message: str,
    current_exam_target: Optional[str] = None,
) -> Tuple[Optional[str], bool]:
    """
    Detect if the user's message mentions a different exam than their target.

    Returns:
        (detected_exam, is_cross_exam)
        - detected_exam: the exam mentioned in the message (canonical name), or None
        - is_cross_exam: True if the detected exam differs from current_exam_target
    """
    if not message:
        return None, False

    msg_lower = message.lower()
    detected = None

    # Check each keyword — longest match first to avoid partial matches
    sorted_keywords = sorted(_EXAM_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        # Word-boundary match to avoid false positives (e.g., "categorical" matching "cat")
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, msg_lower):
            detected = _EXAM_KEYWORDS[keyword]
            break

    if not detected:
        return None, False

    # Check if this is a different exam than the user's target
    is_cross = False
    if current_exam_target:
        current_upper = current_exam_target.strip().upper()
        # Normalize CAT/MBA variants
        if current_upper in ("CAT", "CAT/MBA", "MBA"):
            current_upper = "CAT"
        if detected.upper() != current_upper:
            is_cross = True

    return detected, is_cross


def build_rag_context(
    retrieved_chunks: List[Dict],
    max_context_chars: int = 3000,
) -> str:
    """
    Convert retrieved chunks into a clean context string for the system prompt.

    Args:
        retrieved_chunks: List of {"text": str, "relevance": float, "exam": str}
        max_context_chars: Maximum character length for context block

    Returns:
        Formatted context string, or empty string if no relevant chunks.
    """
    if not retrieved_chunks:
        return ""

    # Sort by relevance (highest first)
    sorted_chunks = sorted(retrieved_chunks, key=lambda c: c.get("relevance", 0), reverse=True)

    # Build context, respecting max length
    parts = []
    total_chars = 0
    for chunk in sorted_chunks:
        text = chunk.get("text", "").strip()
        if not text:
            continue
        if total_chars + len(text) > max_context_chars:
            # Truncate if adding this chunk would exceed limit
            remaining = max_context_chars - total_chars
            if remaining > 100:  # Only add if meaningful amount of text
                parts.append(text[:remaining] + "...")
            break
        parts.append(text)
        total_chars += len(text)

    if not parts:
        return ""

    context = "\n\n".join(parts)
    return f"--- RELEVANT KNOWLEDGE ---\n{context}\n--- END KNOWLEDGE ---"


def build_chatbot_system_prompt(
    exam_target: Optional[str] = None,
    preparation_stage: Optional[str] = None,
    rag_context: str = "",
    cross_exam_detected: Optional[str] = None,
    message_count: int = 0,
) -> str:
    """
    Build the complete Aria chatbot system prompt with RAG context injected.

    Args:
        exam_target: The user's selected exam (e.g., "GMAT")
        preparation_stage: The user's preparation stage
        rag_context: RAG-retrieved knowledge context
        cross_exam_detected: If user asked about a different exam than their target
        message_count: Number of messages exchanged so far (for lead capture timing)
    """

    # Exam context section
    exam_section = ""
    if exam_target:
        exam_section += f"Student is targeting: {exam_target}\n"
    if preparation_stage:
        exam_section += f"Preparation stage: {preparation_stage}\n"

    # Cross-exam hint
    cross_exam_hint = ""
    if cross_exam_detected and exam_target:
        if cross_exam_detected.upper() != (exam_target or "").upper():
            cross_exam_hint = f"""
[CROSS-EXAM NOTE]
The student originally selected {exam_target} but is now asking about {cross_exam_detected}.
Acknowledge this naturally — for example: "I see you're also curious about {cross_exam_detected}! Here's what you should know..."
Do NOT ignore the switch. Answer about {cross_exam_detected} since that's what they asked about.
"""

    # Knowledge base section
    knowledge_section = ""
    if rag_context:
        knowledge_section = f"""
[KNOWLEDGE BASE]
Use the following knowledge to answer the student's question accurately.
{rag_context}
"""

    # Lead capture timing hint — conversational (no UI form)
    lead_timing = ""
    if message_count < 3:
        lead_timing = """
- The conversation just started. Focus ONLY on answering questions helpfully.
- Do NOT ask for contact details yet. Build trust first by providing genuine value."""
    elif message_count < 6:
        lead_timing = """
- You've provided some good answers. After answering their current question well, you may naturally mention:
  "I'd love to have our counselor share a personalized study plan with you! Could you share your name, WhatsApp number, and email address?"
- But ONLY if the conversation flows naturally toward it. Don't force it."""
    else:
        lead_timing = """
- The student has been engaged for several messages. You can now warmly ask for their contact details IN THE CONVERSATION:
  "You're asking really great questions! I'd love to connect you with a senior counselor for a personalized plan. Can I get your name, WhatsApp number, and email address?"
- If they share their details, thank them warmly and confirm a counselor will reach out.
- If they haven't shared yet and seem interested, ask gently one more time."""

    prompt = f"""You are Aria, an AI Academic Advisor for a premium coaching institute specializing in competitive exam preparation.

[YOUR ROLE]
- You help students with information about competitive exams: UPSC, JEE, NEET, CAT/MBA, and GMAT
- You provide detailed, accurate information about exam patterns, syllabus, strategy, fees, and preparation plans
- You act as a knowledgeable, warm, and encouraging academic counselor
- You help students understand which courses and preparation approaches are best for them

[EXAM CONTEXT]
{exam_section if exam_section else "No specific exam target identified yet. Help the student explore options."}
{cross_exam_hint}{knowledge_section}
[RESPONSE RULES]
1. Give detailed, helpful responses of 4-6 sentences minimum
2. Base your answers on the KNOWLEDGE BASE above when available
3. If the answer is in the knowledge base, use that information directly — do NOT deflect or redirect to a counselor
4. If the answer is NOT in the knowledge base, provide your best general knowledge but suggest connecting with a counselor for specifics
5. End each response with a relevant follow-up question to keep the conversation going
6. If the student asks about fees or pricing, ALWAYS give the fee ranges from the knowledge base. NEVER deflect fee questions — students deserve transparent pricing information
7. After providing value (3+ exchanges), you may naturally ask for the student's name, WhatsApp number, and email address IN THE CONVERSATION to connect them with a counselor. Ask conversationally like: "Can I get your name, WhatsApp number, and email so our counselor can share a personalized plan and schedule a session with you?"
8. Respond in Hinglish if the student writes in Hinglish or Hindi
9. NEVER mention "Data Science", "AI courses", "Python courses", "Digital Marketing", or "Full Stack Web Dev" — you ONLY deal with competitive exams
10. If asked something completely outside your domain, say: "I specialize in competitive exam guidance. Let me connect you with a counselor who can help with that!"
11. Be warm, encouraging, and empathetic — many students are stressed about exam preparation

[LEAD CAPTURE TIMING]
{lead_timing}

[PERSONALITY]
- Name: Aria
- Tone: Friendly, knowledgeable, encouraging, professional
- Style: Like a supportive senior who has been through the exam preparation journey
- Never be dismissive of a student's concerns or doubts
- Celebrate the student's decision to prepare and motivate them"""

    return prompt
