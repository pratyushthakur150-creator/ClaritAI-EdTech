"""
Teaching Assistant Service - RAG + Voice doubt-solving.
Pipeline: Student audio -> Groq Whisper STT (API) -> ChromaDB RAG -> GPT-4o-mini -> TTS.
"""
import os
import time
import uuid
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
EMBEDDING_MODEL = "text-embedding-3-small"

# ΓöÇΓöÇ Groq client for Whisper API ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
try:
    from groq import Groq as GroqClient
except ImportError:
    GroqClient = None

GROQ_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")

# ΓöÇΓöÇ Shared local Whisper model (fallback STT) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
_LOCAL_WHISPER_MODEL = None


def load_whisper_model():
    """
    Load a shared local Whisper model (openai-whisper) for fallback STT.

    This is used when Groq Whisper returns clearly hallucinated output
    (e.g. always 'Thank you.' regardless of input), and is also reused
    by ContentIndexingService for video transcription.
    """
    global _LOCAL_WHISPER_MODEL
    if _LOCAL_WHISPER_MODEL is not None:
        return _LOCAL_WHISPER_MODEL

    try:
        import whisper  # type: ignore
        import torch  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Local Whisper fallback not available. "
            "Install openai-whisper and torch in the backend environment."
        ) from e

    # Map Groq-style model names to openai-whisper model names
    env_model = os.getenv("LOCAL_WHISPER_MODEL", os.getenv("WHISPER_MODEL", "base"))
    groq_to_whisper = {
        "whisper-large-v3-turbo": "large-v3-turbo",
        "whisper-large-v3": "large-v3",
        "whisper-large-v2": "large-v2",
        "whisper-large": "large",
    }
    model_name = groq_to_whisper.get(env_model, env_model)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading local Whisper model '{model_name}' on {device} for STT fallback...")
    _LOCAL_WHISPER_MODEL = whisper.load_model(model_name, device=device)
    return _LOCAL_WHISPER_MODEL


class TeachingAssistantService:
    def __init__(self, db: Session, openai_client=None, chroma_client=None, whisper_model=None):
        self.db = db
        self.openai_client = openai_client
        self.chroma_client = chroma_client
        self._whisper_model_name = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
        # Use absolute path anchored to the backend root (fixes CWD mismatch with --reload)
        _backend_root = Path(__file__).resolve().parent.parent.parent  # .../ravian-backend
        self.audio_output_path = _backend_root / "storage" / "audio" / "tts"
        self.audio_output_path.mkdir(parents=True, exist_ok=True)

        # Groq client for Whisper API
        groq_api_key = os.getenv("GROQ_API_KEY")
        if GroqClient and groq_api_key:
            self._groq_client = GroqClient(api_key=groq_api_key)
            logger.info(f"TeachingAssistantService initialized | whisper={self._whisper_model_name} via Groq API")
        else:
            self._groq_client = None
            logger.warning("TeachingAssistantService: GROQ_API_KEY not set ΓÇö voice transcription will fail")

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe student audio using Groq Whisper API.

        Audio file is deleted after transcription for privacy (architecture requirement).

        Optionally converts WebM -> WAV (via pydub/ffmpeg) before calling Groq to avoid
        codec / container issues with browser-recorded WebM.

        Args:
            audio_file_path: Path to temporary audio file (WAV/WebM/MP3 etc.)

        Returns:
            str: Transcribed text

        Raises:
            RuntimeError: If transcription fails
        """
        original_path = Path(audio_file_path)
        working_path = original_path
        extra_temp_paths = []

        try:
            if not self._groq_client:
                raise RuntimeError("Groq client not configured. Set GROQ_API_KEY in .env")

            # Optional debug hook: keep a copy of the raw student audio for manual inspection.
            # Enabled only when TA_DEBUG_AUDIO=1 to preserve privacy by default.
            debug_audio = os.getenv("TA_DEBUG_AUDIO", "").lower() in {"1", "true", "yes"}
            if debug_audio:
                try:
                    debug_dir = self.audio_output_path.parent / "debug" / "stt_raw"
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_copy = debug_dir / original_path.name
                    import shutil
                    shutil.copy2(str(original_path), str(debug_copy))
                    logger.info(
                        f"≡ƒÉ₧ Debug audio copy saved: {debug_copy} "
                        f"({debug_copy.stat().st_size if debug_copy.exists() else 0} bytes)"
                    )
                except Exception as dbg_e:
                    logger.warning(f"ΓÜá∩╕Å Could not save debug audio copy: {dbg_e}")

            # If the browser sent WebM (common for MediaRecorder + Opus), convert to WAV so Groq
            # always receives a simple PCM container regardless of client/browser codec quirks.
            if original_path.suffix.lower() == ".webm":
                try:
                    logger.info(f"≡ƒÄº Converting WebM -> WAV for Whisper via ffmpeg: {original_path}")
                    import tempfile as _tempfile
                    with _tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                        wav_path = Path(tmp_wav.name)
                    ffmpeg_bin = os.getenv("FFMPEG_PATH", "ffmpeg")
                    cmd = [
                        ffmpeg_bin,
                        "-y",
                        "-i",
                        str(original_path),
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        "-vn",
                        str(wav_path),
                    ]
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if result.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size == 0:
                        logger.warning(
                            "ΓÜá∩╕Å ffmpeg WebM->WAV conversion failed "
                            f"(code={result.returncode}): {result.stderr[-400:]}"
                        )
                    else:
                        working_path = wav_path
                        extra_temp_paths.append(str(working_path))
                        logger.info(
                            f"≡ƒÄº WebM->WAV conversion done: {original_path.name} -> "
                            f"{working_path.name} ({working_path.stat().st_size} bytes)"
                        )
                except Exception as conv_e:
                    logger.warning(
                        f"ΓÜá∩╕Å WebM->WAV conversion error, sending original file to Groq: {conv_e}"
                    )
                    working_path = original_path

            logger.info(
                f"≡ƒÄñ Transcribing audio via Groq API (model={self._whisper_model_name}, "
                f"file={working_path.name}, size={working_path.stat().st_size} bytes)..."
            )
            start_time = time.time()

            with open(working_path, "rb") as audio_file:
                transcription = self._groq_client.audio.transcriptions.create(
                    file=(working_path.name, audio_file.read()),
                    model=self._whisper_model_name,
                    # Let Whisper auto-detect language; forcing 'en' can sometimes
                    # produce generic outputs on noisy/non-English audio.
                    response_format="json"
                )

            # When response_format="json", Groq returns an object with a .text field
            if isinstance(transcription, str):
                text = transcription.strip()
            else:
                # Groq's Python client exposes the text as an attribute
                text = getattr(transcription, "text", "") or ""
                text = text.strip()
            transcription_time = time.time() - start_time

            logger.info(f"Γ£à Groq transcribed {len(text)} chars in {transcription_time:.2f}s")
            logger.info(f"≡ƒô¥ Whisper transcription preview (Groq): {text[:120]!r}")

            # If Groq clearly hallucinated (e.g. always 'Thank you.'), fall back to
            # local Whisper for a second opinion.
            normalized = text.strip().lower().strip(".!? ")
            if not text or normalized == "thank you":
                try:
                    logger.warning(
                        "ΓÜá∩╕Å Groq Whisper returned a low-confidence / generic transcription "
                        f"({len(text)} chars: {text!r}). Falling back to local Whisper model..."
                    )
                    local_model = load_whisper_model()
                    # Local Whisper can consume the same WAV file; we keep sample rate at 16k.
                    fallback_result = local_model.transcribe(str(working_path), verbose=False)
                    fallback_text = (fallback_result.get("text") or "").strip()
                    logger.info(
                        f"Γ£à Local Whisper fallback transcription: "
                        f"{len(fallback_text)} chars, preview={fallback_text[:120]!r}"
                    )
                    if fallback_text:
                        return fallback_text
                    # If fallback also fails, keep the original Groq text
                    logger.warning("ΓÜá∩╕Å Local Whisper returned empty text; using Groq transcription.")
                except Exception as fb_e:
                    logger.error(f"Γ¥î Local Whisper fallback failed: {fb_e}")

            return text

        except Exception as e:
            logger.error(f"Γ¥î Audio transcription failed: {e}")
            raise RuntimeError(f"Audio transcription failed: {e}")

        finally:
            # Security: delete student audio immediately after transcription
            # This is a CRITICAL privacy requirement from architecture doc
            for path_str in {str(original_path), *extra_temp_paths}:
                try:
                    if os.path.exists(path_str):
                        os.unlink(path_str)
                        logger.debug(f"≡ƒùæ∩╕Å  Deleted temp audio: {path_str}")
                except Exception as del_e:
                    logger.warning(f"ΓÜá∩╕Å  Could not delete temp audio {path_str}: {del_e}")

    async def _embed_query(self, query: str) -> List[float]:
        if not self.openai_client:
            raise RuntimeError("OpenAI client not configured")
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[query]
        )
        return response.data[0].embedding

    async def search_course_context(
        self, query: str, tenant_id: str, course_id: str, top_k: int = 4
    ) -> List[Dict]:
        if not self.chroma_client:
            return []
        try:
            collection_name = f"tenant_{str(tenant_id)}_course_{str(course_id)}".replace("-", "_")
            collection = self.chroma_client.get_collection(name=collection_name)
            query_embedding = await self._embed_query(query)
            count = collection.count()
            if count == 0:
                return []
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"]
            )
            sources = []
            if results.get('documents') and results['documents'][0]:
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results.get('distances', [[0]*len(results['documents'][0])])[0]
                ):
                    sources.append({
                        'chunk_text': doc,
                        'document_title': meta.get('document_title', 'Course Material'),
                        'document_type': meta.get('document_type', 'unknown'),
                        'source_file': meta.get('source_file', ''),
                        'page_number': meta.get('page_number', ''),
                        'timestamp_label': meta.get('timestamp_label', ''),
                        'relevance_score': 1 - float(dist) if dist else 1.0,
                    })
            return sources
        except Exception as e:
            logger.warning(f"ChromaDB search failed: {e}")
            return []

    async def generate_answer(self, question: str, context_sources: List[Dict], history: List[Dict] = None) -> Dict[str, Any]:
        if not self.openai_client:
            raise RuntimeError("OpenAI client not configured")
        rag_used = len(context_sources) > 0
        if rag_used:
            context_parts = []
            for i, s in enumerate(context_sources, 1):
                loc = f" (Page {s['page_number']})" if s.get('page_number') else (
                    f" (at {s['timestamp_label']})" if s.get('timestamp_label') else ""
                )
                context_parts.append(f"[Source {i}: {s['document_title']}{loc}]\n{s['chunk_text']}")
            context_text = "\n\n---\n\n".join(context_parts)
            system_prompt = f"""SYSTEM PROMPT - CLARIT AI TEACHING ASSISTANT (SAT PREP)
=============================================================

You are Ravi, an AI SAT Teaching Assistant built by Clarit AI,
deployed for ClaritAI - a premium SAT coaching platform led by
top-scoring mentors. You are available 24x7 to help enrolled
students with their SAT prep.

Your ONLY job is to help students understand SAT concepts, solve
problems, and improve their scores. You are NOT a sales bot.

Powered by: Clarit AI | Deployed for: ClaritAI SAT Prep

========================================
HOW YOU USE CONTEXT (IMPORTANT)
========================================

You are given:
1) The student's question.
2) A set of course snippets under "Course Material" below, each
   tagged as [Source i: ...] and sometimes with page/timestamp info.

Your rules:
- Treat these snippets as the ONLY authoritative source for
  explanations and answers whenever they are relevant.
- Explicitly CITE sources in your explanation (e.g. "From Source 2...").
- If the answer is NOT in the provided material, say this clearly
  and then answer using your SAT expertise, but mention that it is
  based on general knowledge and not the uploaded course content.

========================================
YOUR SAT EXPERTISE
========================================

READING & WRITING
- Reading Comprehension: Main idea, Detail, Inference,
  Vocabulary in Context, Text Structure, Purpose.
- Standard English Conventions: Grammar, Punctuation,
  Sentence Structure, Usage.
- Expression of Ideas: Rhetorical Synthesis, Transitions.
- Approach: Teach frameworks, not just answers.
  Explain WHY wrong options are wrong.

MATH
- Algebra: Linear equations, Systems of equations,
  Linear functions, Inequalities.
- Advanced Math: Quadratic equations, Polynomial functions,
  Exponential functions, Radicals, Rational expressions.
- Problem Solving & Data Analysis: Ratios, Rates, Proportions,
  Percentages, Statistics, Probability, Data interpretation.
- Geometry & Trigonometry: Area, Volume, Lines, Angles,
  Circles, Triangles, Right triangle trig.
- Approach: Always show step-by-step working.
  Offer 2 methods where possible (algebraic + intuitive).

========================================
HOW YOU TEACH
========================================

When a student shares a question or concept doubt:

1. UNDERSTAND - Briefly restate what they are asking.

2. EXPLAIN THE CONCEPT - Briefly explain the underlying concept
   or trap being tested, using the Course Material above.

3. SOLVE STEP BY STEP - Show full working and number each step.

4. EXPLAIN THE ANSWER - Explain WHY the correct answer is correct.
   For Reading & Writing, explain why each wrong option is wrong.

5. GIVE A TIP - End with a memory trick, common pattern, or trap.

6. CHECK UNDERSTANDING - End with: "Does this make sense?
   Want me to give you a similar practice question?"

========================================
RESPONSE FORMAT
========================================

Your answers must be clean, readable PLAIN TEXT.
Do NOT use markdown symbols like "#", "##", "###", "**", "_", or LaTeX.
Do NOT use backslash-parentheses, backslash-brackets, or boxed notation.
Write math expressions in plain text, e.g. "x^2 + 3x - 4 = 0".
Use simple numbering, short section titles, and line breaks.

========================================
TONE & STYLE
========================================

- Warm, patient, and encouraging.
- Never make the student feel bad for not knowing something.
- Celebrate good thinking and partial progress.
- Keep explanations concise but complete.

========================================
SAT EXAM FACTS (ALWAYS ACCURATE)
========================================

Digital SAT (current version, since March 2024):
- Total Score: 400-1600.
- 2 Sections:
  Reading & Writing (54 Qs, 64 min, 2 modules),
  Math (44 Qs, 70 min, 2 modules).
- Adaptive: Module 2 difficulty based on Module 1 performance.
- Calculator allowed on ALL math questions.
- No penalty for wrong answers - always guess if unsure.

Common score targets:
- Ivy League / Top 20: typically 1500+.
- Top 50 universities: typically 1400-1500.
- Competitive admits: 1300-1400 with a strong profile.

========================================
ESCALATION TO HUMAN MENTOR
========================================

Escalate to a human mentor when:
- The student is stuck on the same concept after 2-3 attempts.
- The question involves an official SAT problem with a disputed explanation.
- The student asks for a detailed, personalized study plan.
- The student expresses significant stress or anxiety.

========================================
WHAT YOU DO NOT DO
========================================

- Do NOT just give the answer without explanation.
- Do NOT skip showing your working.
- Do NOT answer questions unrelated to SAT or college admissions.
- Do NOT guarantee a specific score improvement.
- Do NOT fabricate official SAT problems.
- Do NOT mention any AI company other than Clarit AI.

========================================
COURSE MATERIAL (RAG CONTEXT)
========================================

Below is the course material. Use it as your primary reference:

Course Material:
{context_text}"""
        else:
            system_prompt = """SYSTEM PROMPT - CLARIT AI TEACHING ASSISTANT (SAT PREP)
=============================================================

You are Ravi, an AI SAT Teaching Assistant built by Clarit AI,
deployed for ClaritAI - a premium SAT coaching platform led by
top-scoring mentors. You are available 24x7 to help enrolled
students with their SAT prep.

Right now, there is no course material indexed for this student
or course, so you CANNOT reference any uploaded notes or PDFs.
Answer using your SAT expertise, but clearly state that you are
answering from general knowledge, not from the student's material.

Keep the same SAT expertise, teaching style, tone, escalation
rules, and "what you do not do" constraints as in the main prompt.

Your answers must be clean, readable PLAIN TEXT.
Do NOT use markdown symbols like "#", "##", "###", "**", "_", or LaTeX.
Do NOT use backslash-parentheses, backslash-brackets, or boxed notation.
Write math expressions in plain text, e.g. "x^2 + 3x - 4 = 0".
Use numbered lists (1. 2. 3.) for steps.
Use line breaks to separate sections.
"""

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Append prior conversation history (cap at last 20 messages to respect token limits)
        if history:
            safe_history = history[-20:]
            for msg in safe_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Append the current question
        messages.append({"role": "user", "content": question})

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip()
        confidence = min(0.95, 0.5 + len(context_sources) * 0.1) if rag_used else 0.4
        return {'answer': answer, 'confidence': confidence, 'rag_used': rag_used, 'sources': context_sources}

    async def generate_vision_answer(
        self, question: str, image_base64: str, image_media_type: str,
        context_sources: List[Dict]
    ) -> Dict[str, Any]:
        """Use GPT-4o vision to analyze an image alongside course context."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not configured")

        rag_used = len(context_sources) > 0
        if rag_used:
            context_parts = []
            for i, s in enumerate(context_sources, 1):
                loc = f" (Page {s['page_number']})" if s.get('page_number') else (
                    f" (at {s['timestamp_label']})" if s.get('timestamp_label') else ""
                )
                context_parts.append(f"[Source {i}: {s['document_title']}{loc}]\n{s['chunk_text']}")
            context_text = "\n\n---\n\n".join(context_parts)
            system_prompt = f"""You are Ravi, the SAT AI Teaching Assistant built by Clarit AI.

The student has uploaded an image (e.g. a SAT question, diagram, or problem)
and may also have typed a question. You receive:
1) The image (rendered separately), and
2) Course Material snippets below, tagged as [Source i: ΓÇª].

Your job:
- Carefully read the image and understand the question or information shown.
- Use BOTH the image and the Course Material below to answer.
- Explain step by step, as a SAT tutor would.
- Cite sources from the Course Material when you use them.
- If the material below does not cover the image content, say so and then answer
  using your SAT expertise.

Keep the same teaching style, tone, escalation rules, and SAT constraints
as in the main text prompt.

FORMATTING RULES (CRITICAL — follow these exactly):
- Do NOT use markdown symbols like "#", "##", "###", "**", "_", or LaTeX.
- Do NOT use \\( \\), \\[ \\], \\boxed{{}}, or any LaTeX math notation.
- Write math expressions in plain text, e.g. "x^2 + 3x - 4 = 0" or "sqrt(64)".
- Use numbered lists (1. 2. 3.) for steps.
- Use line breaks to separate sections.
- Keep formatting clean and readable as plain text.

Course Material:
{context_text}"""
        else:
            system_prompt = """You are Ravi, the SAT AI Teaching Assistant built by Clarit AI.

The student has uploaded an image (e.g. a SAT question, diagram, or problem).
There is currently no indexed course material for this student, so you must
answer using only what you can see in the image and your SAT expertise.

Analyze the image carefully and:
- Restate what the question or information is.
- Solve step by step, as a SAT tutor would.
- Explain why the correct answer is correct and, where relevant, why other
  options are wrong.

FORMATTING RULES (CRITICAL — follow these exactly):
- Do NOT use markdown symbols like "#", "##", "###", "**", "_", or LaTeX.
- Do NOT use \\( \\), \\[ \\], \\boxed{{}}, or any LaTeX math notation.
- Write math expressions in plain text, e.g. "x^2 + 3x - 4 = 0" or "sqrt(64)".
- Use numbered lists (1. 2. 3.) for steps.
- Use line breaks to separate sections.
- Keep formatting clean and readable as plain text.

Keep the same teaching style, tone, escalation rules, and constraints
as in the main text prompt.
"""

        # Build GPT-4o vision message with image + text
        user_content = []
        # Add the image
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{image_media_type};base64,{image_base64}",
                "detail": "high"
            }
        })
        # Add the text question
        if question.strip():
            user_content.append({"type": "text", "text": question})
        else:
            user_content.append({"type": "text", "text": "Please analyze this image and explain or solve what's shown."})

        logger.info(f"≡ƒû╝∩╕Å Sending image to GPT-4o vision (question: {question[:80]}...)")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",  # GPT-4o supports vision; gpt-4o-mini does NOT
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip()
        confidence = min(0.95, 0.6 + len(context_sources) * 0.1) if rag_used else 0.5
        logger.info(f"≡ƒû╝∩╕Å GPT-4o vision response: {len(answer)} chars")
        return {'answer': answer, 'confidence': confidence, 'rag_used': rag_used, 'sources': context_sources}

    async def process_image_query(
        self,
        student_id: str,
        course_id: str,
        tenant_id: str,
        question: str,
        image_bytes: bytes,
        image_filename: str,
        module_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full pipeline: image + optional text ΓåÆ RAG ΓåÆ GPT-4o vision ΓåÆ answer."""
        import base64
        from app.models.student_interaction import StudentInteraction, InteractionMode

        # Determine media type from filename
        ext = image_filename.rsplit('.', 1)[-1].lower() if '.' in image_filename else 'png'
        media_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                     'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp'}
        image_media_type = media_map.get(ext, 'image/png')

        # Base64-encode the image for GPT-4o vision API
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Use text question for RAG search (if provided)
        search_query = question.strip() if question.strip() else "image question"
        sources = await self.search_course_context(search_query, tenant_id, course_id)

        # Generate answer with GPT-4o vision
        result = await self.generate_vision_answer(question, image_base64, image_media_type, sources)

        # Save interaction (gracefully handle DB errors — e.g. dummy student_id)
        interaction_id = None
        try:
            interaction = StudentInteraction(
                tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
                student_id=UUID(student_id) if isinstance(student_id, str) else student_id,
                course_id=UUID(course_id) if isinstance(course_id, str) else course_id,
                module_id=UUID(module_id) if module_id else None,
                query=f"[Image: {image_filename}] {question}",
                answer=result['answer'],
                mode=InteractionMode.TEXT,
                sources=result['sources'],
                confidence=result['confidence']
            )
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            interaction_id = str(interaction.id)
        except Exception as db_err:
            self.db.rollback()
            logger.warning(f"⚠️ Could not save image query interaction: {db_err}")
            interaction_id = str(uuid.uuid4())  # generate a placeholder ID

        sources_resp = [
            {
                'document_title': s.get('document_title', ''),
                'document_type': s.get('document_type', ''),
                'source_file': s.get('source_file', ''),
                'page_number': str(s.get('page_number', '')),
                'timestamp_label': str(s.get('timestamp_label', '')),
                'relevance_score': s.get('relevance_score'),
            }
            for s in result['sources']
        ]
        return {
            'interaction_id': interaction_id,
            'question': question or f"[Image: {image_filename}]",
            'answer': result['answer'],
            'sources': sources_resp,
            'confidence': result['confidence'],
            'rag_used': result['rag_used'],
            'audio_url': None
        }

    async def generate_tts_response(self, text: str, voice: str = "nova") -> Optional[str]:
        if not self.openai_client:
            logger.warning("TTS skipped: OpenAI client not available (check OPENAI_API_KEY)")
            return None
        try:
            audio_filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
            audio_path = self.audio_output_path / audio_filename
            logger.info(f"Generating TTS: voice={voice}, text_length={len(text)}, output={audio_path}")
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=1.0
            )
            response.stream_to_file(str(audio_path))
            # Verify file was written
            import os as _os
            file_size = _os.path.getsize(str(audio_path)) if audio_path.exists() else 0
            audio_url = f"/api/v1/teaching-assistant/audio/{audio_filename}"
            logger.info(f"TTS generated: {audio_url} ({file_size} bytes)")
            if file_size == 0:
                logger.error("TTS file is empty ΓÇö audio playback will fail")
                return None
            return audio_url
        except Exception as e:
            logger.error(f"TTS failed: {e}", exc_info=True)
            return None

    async def process_text_query(
        self,
        student_id: str,
        course_id: str,
        tenant_id: str,
        question: str,
        module_id: Optional[str] = None,
        use_voice_response: bool = False,
        voice_id: str = "nova"
    ) -> Dict[str, Any]:
        from app.models.student_interaction import StudentInteraction, InteractionMode

        sources = await self.search_course_context(question, tenant_id, course_id)
        result = await self.generate_answer(question, sources)
        audio_url = None
        if use_voice_response:
            audio_url = await self.generate_tts_response(result['answer'], voice=voice_id)

        interaction = StudentInteraction(
            tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            student_id=UUID(student_id) if isinstance(student_id, str) else student_id,
            course_id=UUID(course_id) if isinstance(course_id, str) else course_id,
            module_id=UUID(module_id) if module_id else None,
            query=question,
            answer=result['answer'],
            mode=InteractionMode.MIXED if use_voice_response else InteractionMode.TEXT,
            audio_url=audio_url,
            sources=result['sources'],
            confidence=result['confidence']
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)

        sources_resp = [
            {
                'document_title': s.get('document_title', ''),
                'document_type': s.get('document_type', ''),
                'source_file': s.get('source_file', ''),
                'page_number': str(s.get('page_number', '')),
                'timestamp_label': str(s.get('timestamp_label', '')),
                'relevance_score': s.get('relevance_score'),
            }
            for s in result['sources']
        ]
        return {
            'interaction_id': str(interaction.id),
            'question': question,
            'answer': result['answer'],
            'sources': sources_resp,
            'confidence': result['confidence'],
            'rag_used': result['rag_used'],
            'audio_url': audio_url
        }

    async def process_voice_query(
        self,
        student_id: str,
        course_id: str,
        tenant_id: str,
        audio_file_path: str,
        module_id: Optional[str] = None,
        voice_id: str = "nova"
    ) -> Dict[str, Any]:
        question = await self.transcribe_audio(audio_file_path)
        result = await self.process_text_query(
            student_id=student_id,
            course_id=course_id,
            tenant_id=tenant_id,
            question=question,
            module_id=module_id,
            use_voice_response=True,
            voice_id=voice_id
        )
        result['transcribed_question'] = question
        return result

    async def submit_feedback(
        self,
        interaction_id: str,
        tenant_id: str,
        rating: int,
        comment: Optional[str] = None,
        helpful: Optional[bool] = None
    ) -> Dict:
        from app.models.student_interaction import StudentInteraction

        iid = UUID(interaction_id) if isinstance(interaction_id, str) else interaction_id
        tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        interaction = self.db.query(StudentInteraction).filter(
            StudentInteraction.id == iid,
            StudentInteraction.tenant_id == tid
        ).first()
        if not interaction:
            raise ValueError(f"Interaction {interaction_id} not found")
        interaction.update_feedback(rating, comment)
        self.db.commit()
        return {'interaction_id': interaction_id, 'feedback_saved': True, 'rating': rating}
