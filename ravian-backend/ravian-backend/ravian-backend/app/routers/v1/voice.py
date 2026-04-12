# voice.py - FastAPI router for voice-related endpoints
import os
import json
import uuid
from uuid import UUID
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import httpx
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Path as FastAPIPath
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from app.services.voice_service import VoiceService
from app.services.assistant_service import AssistantService
from app.services.vapi_service import VAPIService

from pydantic import BaseModel, Field, validator
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

from app.dependencies.auth import get_current_user
from app.core.database import get_db_session
from sqlalchemy.orm import Session
from app.models.enrollment import Enrollment, Student
from app.models.lead import Lead

load_dotenv()

# Configure logging (must be before first logger usage)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Voice router: FastAPI dependencies loaded")

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Configuration — use the same secret as the main app
try:
    from app.core.config import settings as app_settings
    JWT_SECRET = app_settings.jwt_secret_key
except Exception:
    JWT_SECRET = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET_KEY is not set — refusing to start with insecure default")
JWT_ALGORITHM = 'HS256'
ALLOWED_AUDIO_TYPES = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 'audio/webm', 'audio/ogg', 'audio/flac']
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "audio_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize services
voice_service = VoiceService()
# AssistantService will auto-detect OpenAI key and disable demo mode
assistant_service = AssistantService(voice_service=voice_service, demo_mode=False)
vapi_service = VAPIService()

@router.get("/audio/{tenant_id}/{filename}")
async def get_audio_file(tenant_id: str, filename: str):
    """Serve generated audio files"""
    base_dir = Path(os.getcwd())
    file_path = base_dir / "uploads" / "audio_responses" / tenant_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path)

# TODO(production): Replace in-memory conversation store with Redis for
# persistence across restarts and support for multiple Uvicorn workers.
conversations: Dict[str, Dict] = {}

# Pydantic models
class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000, description="Text to convert to speech")
    voice_id: str = Field(default='alloy', description="Voice ID to use for synthesis")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")
    format: str = Field(default='mp3', description="Audio format")
    
    @validator('voice_id')
    def validate_voice(cls, v):
        allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        if v not in allowed_voices:
            raise ValueError(f'Voice must be one of: {allowed_voices}')
        return v

class ConversationRequest(BaseModel):
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    voice_settings: Dict[str, Any] = Field(default_factory=dict, description="Voice configuration")

class VoiceInfo(BaseModel):
    id: str
    name: str
    description: str
    gender: str
    language: str
    sample_rate: int = 24000

class TranscriptionResponse(BaseModel):
    transcript: str
    confidence: float
    duration: float
    language: str
    file_size: int
    student_id: str
    tenant_id: str
    timestamp: str

class SynthesisResponse(BaseModel):
    audio_url: str
    filename: str
    duration: float
    file_size: int
    voice_id: str
    speed: float
    tenant_id: str
    timestamp: str

class ConversationResponse(BaseModel):
    session_id: str
    status: str
    student_id: str
    course_id: str
    voice_settings: Dict[str, Any]
    created_at: str
    tenant_id: str

class ConversationMessageResponse(BaseModel):
    interaction_id: str
    session_id: str
    turn_number: int
    transcript: str
    answer_text: str
    audio_url: Optional[str]
    audio_duration: Optional[float]
    confidence_score: float
    processing_time: float
    timestamp: str


class OutboundCallRequest(BaseModel):
    """Request schema for initiating an outbound intelligence call via VAPI."""
    phone_number: str = Field(..., description="E.164 formatted destination phone number")
    assistant_id: str = Field(..., description="VAPI assistant ID to use for the call")
    student_id: Optional[str] = Field(None, description="Optional student ID to link the call to")
    lead_id: Optional[str] = Field(None, description="Optional lead ID to link the call to")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata to send to VAPI",
    )

def validate_student_access(student_id: str, tenant_id: str, db: Session, require_voice: bool = False) -> Dict:
    """Validate student belongs to tenant and has required permissions"""
    try:
        student_uuid = UUID(student_id) if isinstance(student_id, str) else student_id
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid student ID format")

    student_record = db.query(Student).join(Lead).filter(
        Student.id == student_uuid,
        Student.tenant_id == tenant_id
    ).first()

    if not student_record:
        # Fallback: check if student_id is an enrollment_id
        enrollment = db.query(Enrollment).join(Lead).filter(
            Enrollment.id == student_uuid,
            Enrollment.tenant_id == tenant_id
        ).first()
        
        if enrollment:
            # If it's an enrollment, we can still proceed
            return {
                'id': str(enrollment.id),
                'tenant_id': str(enrollment.tenant_id),
                'name': enrollment.lead.name if enrollment.lead else "Student",
                'voice_enabled': True # Assume enabled for enrollments for now
            }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    student_data = {
        'id': str(student_record.id),
        'tenant_id': str(student_record.tenant_id),
        'name': student_record.lead.name if student_record.lead else "Student",
        'voice_enabled': True # In real implementation, check a flag
    }
    
    logger.info(f"Student access validated: {student_id} in tenant {tenant_id}")
    return student_data

async def save_uploaded_file(upload_file: UploadFile, tenant_id: str) -> Path:
    """Save uploaded audio file and return file path"""
    if upload_file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Allowed: {ALLOWED_AUDIO_TYPES}"
        )
    
    if upload_file.size and upload_file.size > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)}MB"
        )
    
    # Create tenant-specific directory
    tenant_dir = UPLOAD_DIR / tenant_id
    tenant_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{file_extension}"
    file_path = tenant_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        
        logger.info(f"File saved: {file_path} ({len(content)} bytes)")
        return file_path
        
    except Exception as e:
        logger.error(f"File save failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file"
        )


@router.post("/outbound-call")
async def create_outbound_call(
    request: OutboundCallRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Initiate an outbound intelligence call via VAPI.

    This endpoint forwards the request to the VAPI API using the configured
    `VAPI_API_KEY` and returns the VAPI response payload.
    """
    tenant_id = str(current_user.get("tenant_id"))

    try:
        # Merge core metadata with any custom fields from the request
        metadata: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "triggered_by_user_id": str(current_user.get("user_id")),
        }
        if request.student_id:
            metadata["student_id"] = request.student_id
        if request.lead_id:
            metadata["lead_id"] = request.lead_id
        if request.metadata:
            metadata.update(request.metadata)

        logger.info(
            f"Initiating VAPI call to {request.phone_number} "
            f"with assistant {request.assistant_id}"
        )

        result = await vapi_service.create_outbound_call(
            phone_number=request.phone_number,
            assistant_id=request.assistant_id,
            metadata=metadata,
        )

        logger.info(f"VAPI call initiated successfully: {result}")

        return {"status": "success", "vapi": result}

    except ValueError as e:
        # Invalid phone number format
        logger.error(f"Invalid phone number format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number: {str(e)}",
        )
    except httpx.HTTPStatusError as e:
        # VAPI API returned an error – surface the detail
        logger.error(f"VAPI API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"VAPI API error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error initiating VAPI call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate call: {str(e)}",
        )

# API Endpoints

@router.get("/calls")
async def list_voice_calls(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    List voice call history for the CRM Voice Agent page.
    Tries to query real call logs; falls back to sample data.
    """
    tenant_id = str(current_user.get("tenant_id"))
    logger.info(f"Voice calls list requested for tenant {tenant_id}")

    calls = []

    # Try to pull real call data from the DB
    try:
        from app.models.call import CallLog
        rows = (
            db.query(CallLog)
            .join(Lead, CallLog.lead_id == Lead.id)
            .filter(Lead.tenant_id == tenant_id)
            .order_by(CallLog.created_at.desc())
            .limit(50)
            .all()
        )
        for row in rows:
            calls.append({
                "id": str(row.id),
                "leadName": row.lead.name if row.lead else "Unknown",
                "phone": row.lead.phone if row.lead else "",
                "duration": f"{(row.duration_seconds or 0) // 60}:{(row.duration_seconds or 0) % 60:02d}" if row.duration_seconds else "-",
                "status": row.outcome or "completed",
                "date": row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else "",
                "summary": row.summary or row.notes or "",
            })

        if calls:
            return {"calls": calls, "total": len(calls)}
    except Exception as e:
        logger.debug(f"Could not query real voice calls: {e}")

    # Fallback sample data
    return {
        "calls": [
            {"id": "1", "leadName": "Arjun Sharma", "phone": "+91 98765 43210", "duration": "4:32", "status": "completed", "date": "2 hours ago", "summary": "Interested in ML course."},
            {"id": "2", "leadName": "Priya Verma", "phone": "+91 87654 32109", "duration": "6:15", "status": "completed", "date": "3 hours ago", "summary": "Enrolled in Data Science."},
            {"id": "3", "leadName": "Neha Malhotra", "phone": "+91 65432 10987", "duration": "-", "status": "scheduled", "date": "Tomorrow 3PM", "summary": "Demo scheduled."},
            {"id": "4", "leadName": "Vikram Singh", "phone": "+91 54321 09876", "duration": "-", "status": "missed", "date": "Yesterday", "summary": "No answer."},
        ],
        "total": 4,
    }

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    student_id: str = Form(..., description="Student ID"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en', 'es')"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload audio file and transcribe to text
    """
    try:
        logger.info(f"Transcription request from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')} for student {student_id}")
        
        # Validate student access
        student = validate_student_access(student_id, current_user.get("tenant_id"), db, require_voice=True)
        
        # Save uploaded file
        file_path = await save_uploaded_file(audio_file, current_user.get("tenant_id"))
        
        # Transcribe audio
        transcription_result = await voice_service.transcribe_audio(
            str(file_path), 
            current_user.get("tenant_id"), 
            language
        )
        
        # Clean up uploaded file
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
        
        response = TranscriptionResponse(
            transcript=transcription_result['transcript'],
            confidence=transcription_result['confidence'],
            duration=transcription_result['duration'],
            language=transcription_result['language'],
            file_size=transcription_result['file_size'],
            student_id=student_id,
            tenant_id=current_user.get("tenant_id"),
            timestamp=transcription_result['timestamp']
        )
        
        logger.info(f"Transcription completed: {len(response.transcript)} characters")
        logger.info(f"Transcription completed for student {student_id}: '{response.transcript[:50]}...'")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription processing failed"
        )

@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Convert text to speech audio
    """
    try:
        logger.info(f"TTS request from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')}: {len(request.text)} characters")
        
        # Generate speech
        tts_result = await voice_service.text_to_speech(
            text=request.text,
            tenant_id=current_user.get("tenant_id"),
            voice=request.voice_id,
            speed=request.speed
        )
        
        response = SynthesisResponse(
            audio_url=tts_result['audio_url'],
            filename=tts_result['filename'],
            duration=tts_result['duration'],
            file_size=tts_result['file_size'],
            voice_id=tts_result['voice_id'],
            speed=tts_result['speed'],
            tenant_id=current_user.get("tenant_id"),
            timestamp=tts_result['timestamp']
        )
        
        logger.info(f"TTS completed: {response.filename} ({response.duration:.1f}s)")
        logger.info(f"Text-to-speech generated: {response.filename} ({response.duration:.1f}s, voice: {response.voice_id})")
        return response
        
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed"
        )

@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    List available TTS voices
    """
    try:
        voices = [
            VoiceInfo(id="alloy", name="Alloy", description="Balanced, neutral voice", gender="neutral", language="en"),
            VoiceInfo(id="echo", name="Echo", description="Clear, professional voice", gender="male", language="en"),
            VoiceInfo(id="fable", name="Fable", description="Warm, storytelling voice", gender="neutral", language="en"),
            VoiceInfo(id="onyx", name="Onyx", description="Deep, authoritative voice", gender="male", language="en"),
            VoiceInfo(id="nova", name="Nova", description="Bright, energetic voice", gender="female", language="en"),
            VoiceInfo(id="shimmer", name="Shimmer", description="Soft, gentle voice", gender="female", language="en"),
        ]
        
        logger.info(f"Voice list requested by {current_user.get('email') or current_user.get('username') or current_user.get('user_id')}")
        logger.info(f"Voice list provided: {len(voices)} voices available")
        return voices
        
    except Exception as e:
        logger.error(f"Voice listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice list"
        )

@router.post("/conversation", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start new voice conversation session
    """
    try:
        logger.info(f"Conversation start request from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')} for student {request.student_id}")
        
        # Validate student access
        student = validate_student_access(request.student_id, current_user.get("tenant_id"), db, require_voice=True)
        
        # Create new conversation session
        session_id = str(uuid.uuid4())
        conversation_data = {
            'session_id': session_id,
            'student_id': request.student_id,
            'course_id': request.course_id,
            'tenant_id': current_user.get("tenant_id"),
            'voice_settings': request.voice_settings,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'turn_count': 0,
            'messages': []
        }
        
        conversations[session_id] = conversation_data
        
        response = ConversationResponse(
            session_id=session_id,
            status='active',
            student_id=request.student_id,
            course_id=request.course_id,
            voice_settings=request.voice_settings,
            created_at=conversation_data['created_at'],
            tenant_id=current_user.get("tenant_id")
        )
        
        logger.info(f"Conversation session created: {session_id}")
        logger.info(f"Conversation session started: {session_id} for student {request.student_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation start failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start conversation"
        )

@router.post("/conversation/{session_id}/message", response_model=ConversationMessageResponse)
async def send_voice_message(
    session_id: str = FastAPIPath(..., description="Conversation session ID"),
    audio_file: UploadFile = File(..., description="Audio message file"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send voice message in conversation
    """
    try:
        logger.info(f"Voice message in session {session_id} from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')}")
        
        # Validate conversation session
        conversation = conversations.get(session_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found"
            )
        
        if conversation['tenant_id'] != current_user.get("tenant_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: conversation not in your tenant"
            )
        
        if conversation['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation session is not active"
            )
        
        # Validate student access
        student = validate_student_access(conversation['student_id'], current_user.get("tenant_id"), db, require_voice=True)
        
        # Save uploaded audio file
        file_path = await save_uploaded_file(audio_file, current_user.get("tenant_id"))
        
        # Process with assistant service
        assistant_response = await assistant_service.answer_query(
            student=student,
            tenant_id=current_user.get("tenant_id"),
            audio_url=str(file_path),
            mode='voice',
            voice_settings=conversation.get('voice_settings', {}),
            return_audio=True
        )
        
        # Update conversation state
        conversation['turn_count'] += 1
        conversation['last_activity'] = datetime.now().isoformat()
        conversation['messages'].append({
            'turn': conversation['turn_count'],
            'timestamp': assistant_response['timestamp'],
            'transcript': assistant_response['query_text'],
            'answer': assistant_response['answer_text'],
            'interaction_id': assistant_response['interaction_id']
        })
        
        # Clean up uploaded file
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
        
        response = ConversationMessageResponse(
            interaction_id=assistant_response['interaction_id'],
            session_id=session_id,
            turn_number=conversation['turn_count'],
            transcript=assistant_response['query_text'],
            answer_text=assistant_response['answer_text'],
            audio_url=assistant_response.get('response_audio_url'),
            audio_duration=assistant_response.get('response_audio_duration'),
            confidence_score=assistant_response['confidence_score'],
            processing_time=assistant_response['processing_time'],
            timestamp=assistant_response['timestamp']
        )
        
        logger.info(f"Voice message processed: turn {conversation['turn_count']} in session {session_id}")
        logger.info(f"Voice message processed: Turn {response.turn_number} - '{response.transcript[:50]}...'")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice message processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice message processing failed"
        )

@router.delete("/conversation/{session_id}")
async def end_conversation(
    session_id: str = FastAPIPath(..., description="Conversation session ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    End conversation session
    """
    try:
        logger.info(f"End conversation request for session {session_id} from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')}")
        
        # Validate conversation session
        conversation = conversations.get(session_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found"
            )
        
        if conversation['tenant_id'] != current_user.get("tenant_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: conversation not in your tenant"
            )
        
        # Update conversation status
        conversation['status'] = 'ended'
        conversation['ended_at'] = datetime.now().isoformat()
        
        # Could archive or cleanup conversation data here
        
        logger.info(f"Conversation session ended: {session_id}")
        logger.info(f"Conversation session ended: {session_id} ({conversation['turn_count']} turns)")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Conversation ended successfully",
                "session_id": session_id,
                "status": "ended",
                "total_turns": conversation['turn_count'],
                "duration": conversation.get('ended_at', datetime.now().isoformat()),
                "ended_by": current_user.get("email") or current_user.get("username") or current_user.get("user_id")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end conversation"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Voice service health check"""
    return {
        "status": "healthy",
        "service": "voice",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": [
            "POST /transcribe",
            "POST /synthesize", 
            "GET /voices",
            "POST /conversation",
            "POST /conversation/{session_id}/message",
            "DELETE /conversation/{session_id}"
        ]
    }