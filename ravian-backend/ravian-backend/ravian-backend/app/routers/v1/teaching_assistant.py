"""Teaching Assistant router - RAG + Voice doubt-solving for students."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import tempfile
import os
import logging
import uuid as _uuid
from pathlib import Path
from typing import Dict, Any

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.schemas.teaching_assistant import (
    TAQueryRequest,
    TAQueryResponse,
    TAFeedbackRequest,
)
from app.services.teaching_assistant_service import TeachingAssistantService
from app.core.config import settings

router = APIRouter(prefix="/teaching-assistant", tags=["Teaching Assistant"])
logger = logging.getLogger(__name__)

# Absolute path to TTS audio directory (same as used by TeachingAssistantService)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # .../ravian-backend
_TTS_AUDIO_DIR = _BACKEND_ROOT / "storage" / "audio" / "tts"

# ── Subject name → deterministic UUID (must match content router) ──
_SUBJECT_NAMESPACE = _uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

def _subject_to_course_id(subject: str) -> str:
    """Convert subject string to deterministic UUID string that matches
    the content router's _subject_to_uuid — so ChromaDB RAG search finds
    documents uploaded for this subject."""
    course_key = subject.lower().replace(" ", "_")
    try:
        _uuid.UUID(course_key)
        return course_key
    except (ValueError, AttributeError):
        return str(_uuid.uuid5(_SUBJECT_NAMESPACE, course_key))


@router.post("/ask")
async def ask_simple_question(
    request: Request,
    body: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Simple text question endpoint for the frontend Teaching Assistant page.
    Accepts {question, subject} and returns {answer}.
    Does NOT create StudentInteraction (no valid UUID for casual chat).
    """
    question = body.get("question", "")
    subject = body.get("subject", "General")
    use_voice = body.get("use_voice", False)
    history = body.get("history", [])  # [{role, content}, ...]

    if not question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    tenant_id = get_tenant_id(current_user)
    service = _get_ta_service(db, request)

    try:
        # Step 1: RAG search for relevant context
        course_id = _subject_to_course_id(subject)
        sources = await service.search_course_context(
            query=question,
            tenant_id=str(tenant_id),
            course_id=course_id,
        )

        # Step 2: Generate answer with GPT
        result = await service.generate_answer(question, sources, history=history)

        # Step 3: Optional TTS
        audio_url = None
        if use_voice:
            audio_url = await service.generate_tts_response(result["answer"])

        return {
            "answer": result.get("answer", "I couldn't generate a response."),
            "subject": subject,
            "sources": result.get("sources", []),
            "audio_url": audio_url,
        }
    except Exception as e:
        logger.error(f"TA /ask failed: {e}", exc_info=True)
        # Return a friendly fallback instead of 500
        return {
            "answer": f"I'm sorry, I encountered an error processing your question about {subject}. Please try again.",
            "subject": subject,
            "sources": [],
            "audio_url": None,
        }



@router.get("/audio/{filename}")
async def serve_tts_audio(filename: str):
    """Serve TTS audio files directly (bypasses StaticFiles mount)."""
    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    file_path = _TTS_AUDIO_DIR / safe_name
    logger.info(f"Audio request: {safe_name} -> {file_path} (exists={file_path.exists()})")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio file not found: {safe_name}")
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=safe_name,
    )


def _get_ta_service(db: Session, request: Request) -> TeachingAssistantService:
    chroma = None
    oai = None
    try:
        import chromadb
        chroma = chromadb.PersistentClient(
            path=os.getenv("CHROMA_DB_PATH", getattr(settings, "chroma_db_path", "./chroma_db"))
        )
    except Exception as e:
        logger.warning(f"ChromaDB unavailable: {e}")
    try:
        from openai import OpenAI
        if settings.openai_api_key:
            oai = OpenAI(api_key=settings.openai_api_key)
    except Exception as e:
        logger.warning(f"OpenAI unavailable: {e}")

    # Inject pre-loaded Whisper model from startup (avoids 20s reload per request)
    whisper_model = getattr(request.app.state, "whisper_model", None)
    return TeachingAssistantService(db=db, openai_client=oai, chroma_client=chroma, whisper_model=whisper_model)


@router.post("/query", response_model=TAQueryResponse)
async def ask_text_question(
    request: Request,
    body: TAQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Text question -> RAG search -> GPT-4o-mini answer (+ optional TTS)."""
    tenant_id = get_tenant_id(current_user)
    service = _get_ta_service(db, request)
    try:
        result = await service.process_text_query(
            student_id=str(body.student_id),
            course_id=str(body.course_id),
            tenant_id=str(tenant_id),
            question=body.question,
            module_id=str(body.module_id) if body.module_id else None,
            use_voice_response=body.use_voice,
            voice_id=body.voice_id
        )
        return TAQueryResponse(**result)
    except Exception as e:
        logger.error(f"TA query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-query")
async def ask_voice_question(
    request: Request,
    student_id: str = Form(...),
    course_id: str = Form(...),
    voice_id: str = Form("nova"),
    audio_file: UploadFile = File(..., description="Audio from browser mic (WAV/WebM)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Voice pipeline: Browser audio -> Whisper STT -> RAG -> GPT-4o-mini -> TTS.
    Does NOT save StudentInteraction (casual chat, no valid UUID).
    """
    import time
    start_time = time.time()

    username = current_user.get("email", "unknown") if isinstance(current_user, dict) else getattr(current_user, "email", "unknown")
    tenant_id = get_tenant_id(current_user)

    logger.info("=" * 80)
    logger.info(f"🎤 VOICE QUERY STARTED by {username}")
    logger.info(f"Course: {course_id} | Voice: {voice_id}")
    logger.info(
        f"Incoming audio: filename={audio_file.filename!r}, "
        f"content_type={audio_file.content_type!r}"
    )
    logger.info("=" * 80)

    # Save to temp file (deleted inside transcribe_audio after STT)
    suffix = ".webm" if "webm" in (audio_file.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    logger.info(f"📁 Saved temp audio: {tmp_path} ({len(content)} bytes)")

    # Reject very short audio — Whisper hallucinates on tiny files (e.g. "Thank you.")
    if len(content) < 5000:
        os.unlink(tmp_path)
        raise HTTPException(
            status_code=400,
            detail="Audio too short — please speak for at least 2 seconds"
        )

    service = _get_ta_service(db, request)

    try:
        # Phase 1: Whisper STT
        logger.info("🔄 Phase 1/4: Whisper transcription starting...")
        question = await service.transcribe_audio(tmp_path)

        # Phase 2: RAG search
        safe_course_id = _subject_to_course_id(course_id)
        logger.info(f"🔄 Phase 2/4: RAG search for: {question[:80]}")
        sources = await service.search_course_context(
            query=question,
            tenant_id=str(tenant_id),
            course_id=safe_course_id,
        )

        # Phase 3: Generate answer
        logger.info("🔄 Phase 3/4: Generating answer...")
        result = await service.generate_answer(question, sources)

        # Phase 4: TTS
        logger.info("🔄 Phase 4/4: Generating TTS audio...")
        audio_url = await service.generate_tts_response(result["answer"], voice=voice_id)

        total_time = time.time() - start_time
        logger.info(f"✅ VOICE QUERY COMPLETED in {total_time:.2f}s")
        logger.info(f"   Transcription: {question}")
        logger.info(f"   Answer length: {len(result.get('answer', ''))} chars")
        logger.info("=" * 80)

        return {
            "question": question,
            "transcribed_question": question,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.5),
            "rag_used": result.get("rag_used", False),
            "audio_url": audio_url,
        }

    except Exception as e:
        # Ensure cleanup if transcribe_audio didn't delete it
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        logger.error(f"❌ Voice TA query failed after {time.time() - start_time:.1f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image-query", response_model=TAQueryResponse)
async def ask_image_question(
    request: Request,
    student_id: str = Form(...),
    course_id: str = Form(...),
    question: str = Form(""),
    image_file: UploadFile = File(..., description="Image of a question, diagram, or problem (JPG/PNG/WebP)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Image + text pipeline: Student photo → GPT-4o Vision → RAG → answer.

    Supports JPG, PNG, WebP, GIF, BMP images up to 10MB.
    The text question is optional — if omitted, the AI will analyze the image.
    """
    import time
    start_time = time.time()

    username = current_user.get("email", "unknown") if isinstance(current_user, dict) else getattr(current_user, "email", "unknown")
    tenant_id = get_tenant_id(current_user)

    logger.info("=" * 80)
    logger.info(f"🖼️ IMAGE QUERY by {username}")
    logger.info(f"Course: {course_id} | Question: {question[:80] if question else '[no text]'}")
    logger.info(f"File: {image_file.filename} | Type: {image_file.content_type}")
    logger.info("=" * 80)

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
    if image_file.content_type and image_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image_file.content_type}. Use JPG, PNG, WebP, GIF, or BMP."
        )

    # Read and validate size
    image_bytes = await image_file.read()
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_bytes) > max_size:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 10MB.")

    logger.info(f"📁 Image read: {image_file.filename} ({len(image_bytes)} bytes)")

    service = _get_ta_service(db, request)

    try:
        result = await service.process_image_query(
            student_id=student_id,
            course_id=course_id,
            tenant_id=str(tenant_id),
            question=question,
            image_bytes=image_bytes,
            image_filename=image_file.filename or "image.png",
        )

        total_time = time.time() - start_time
        logger.info(f"✅ IMAGE QUERY COMPLETED in {total_time:.2f}s")
        logger.info(f"   Answer length: {len(result.get('answer', ''))} chars")
        logger.info("=" * 80)

        return TAQueryResponse(**result)

    except Exception as e:
        logger.error(f"❌ Image TA query failed after {time.time() - start_time:.1f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    request: Request,
    body: TAFeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Submit 1-5 star feedback for a TA interaction."""
    tenant_id = get_tenant_id(current_user)
    service = _get_ta_service(db, request)
    try:
        return await service.submit_feedback(
            interaction_id=str(body.interaction_id),
            tenant_id=str(tenant_id),
            rating=body.rating,
            comment=body.comment,
            helpful=body.helpful
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/interactions/{student_id}")
async def get_student_interactions(
    request: Request,
    student_id: str,
    course_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get recent TA interactions for a student in a course."""
    from app.models.student_interaction import StudentInteraction

    tenant_id = get_tenant_id(current_user)
    interactions = db.query(StudentInteraction).filter(
        StudentInteraction.student_id == student_id,
        StudentInteraction.course_id == course_id,
        StudentInteraction.tenant_id == tenant_id
    ).order_by(StudentInteraction.created_at.desc()).limit(limit).all()
    return {"interactions": [i.to_dict() for i in interactions], "total": len(interactions)}
