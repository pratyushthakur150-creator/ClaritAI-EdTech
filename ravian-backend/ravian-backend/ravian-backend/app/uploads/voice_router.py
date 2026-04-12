# voice.py - FastAPI router for voice-related endpoints
import os
import json
import uuid
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

try:
    from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Path as FastAPIPath
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
except ImportError:
    raise
    from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Path as FastAPIPath
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    raise
    from pydantic import BaseModel, Field, validator

try:
    import jwt
    from jwt.exceptions import InvalidTokenError
except ImportError:
    raise
    import jwt
    from jwt.exceptions import InvalidTokenError

try:
    from dotenv import load_dotenv
except ImportError:
    raise
    from dotenv import load_dotenv

from app.dependencies.auth import get_current_user

load_dotenv()

print("✓ All FastAPI dependencies installed successfully")

# Initialize router
router = APIRouter(tags=["voice"])
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'demo-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ALLOWED_AUDIO_TYPES = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 'audio/webm', 'audio/ogg', 'audio/flac']
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "audio_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mock services and data stores (replace with actual implementations)
class MockVoiceService:
    def __init__(self):
        self.demo_mode = True
        
    async def transcribe_audio(self, file_path: str, tenant_id: str, language: str = None) -> Dict:
        return {
            'transcript': 'This is a demo transcription of the uploaded audio file.',
            'confidence': 0.92,
            'duration': 5.3,
            'language': language or 'en',
            'file_size': 1024 * 50,
            'tenant_id': tenant_id,
            'timestamp': datetime.now().isoformat()
        }
    
    async def text_to_speech(self, text: str, tenant_id: str, voice: str = 'alloy', speed: float = 1.0) -> Dict:
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        return {
            'audio_url': f"/api/v1/voice/audio/{tenant_id}/{audio_filename}",
            'filename': audio_filename,
            'duration': len(text) / 12.0,
            'file_size': len(text) * 80,
            'voice_id': voice,
            'speed': speed,
            'text_length': len(text),
            'tenant_id': tenant_id,
            'timestamp': datetime.now().isoformat()
        }

class MockAssistantService:
    def __init__(self):
        self.demo_mode = True
        
    async def answer_query(self, student, tenant_id: str, query: str = None, audio_url: str = None, 
                          mode: str = 'voice', voice_settings: Dict = None, return_audio: bool = True) -> Dict:
        return {
            'interaction_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'student_id': getattr(student, 'id', 'demo_student'),
            'tenant_id': tenant_id,
            'mode': mode,
            'query_text': query or 'What is machine learning?',
            'answer_text': 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.',
            'response_audio_url': f"/api/v1/voice/audio/{tenant_id}/response_{uuid.uuid4().hex[:8]}.mp3" if return_audio else None,
            'response_audio_duration': 8.5 if return_audio else None,
            'confidence_score': 0.88,
            'sources': [{'id': '1', 'content': 'ML overview content', 'relevance_score': 0.91}],
            'follow_up_questions': ['What are the types of machine learning?', 'How do I get started with ML?'],
            'escalation': {'needed': False, 'reason': None},
            'processing_time': 1.2
        }

# Initialize services
voice_service = MockVoiceService()
assistant_service = MockAssistantService()

# In-memory conversation store (replace with proper database)
conversations: Dict[str, Dict] = {}

# Mock student data
mock_students = {
    'student_1': {'id': 'student_1', 'tenant_id': 'tenant_123', 'voice_enabled': True, 'name': 'John Doe'},
    'student_2': {'id': 'student_2', 'tenant_id': 'tenant_456', 'voice_enabled': True, 'name': 'Jane Smith'},
    'student_3': {'id': 'student_3', 'tenant_id': 'tenant_123', 'voice_enabled': False, 'name': 'Bob Wilson'},
}

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

def validate_student_access(student_id: str, tenant_id: str, require_voice: bool = False) -> Dict:
    """Validate student belongs to tenant and has required permissions"""
    student = mock_students.get(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    if student['tenant_id'] != tenant_id:
        logger.warning(f"Tenant mismatch for student {student_id}: {student['tenant_id']} != {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: student not in your tenant"
        )
    
    if require_voice and not student.get('voice_enabled', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voice features not enabled for this student"
        )
    
    logger.info(f"Student access validated: {student_id} in tenant {tenant_id}")
    return student

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

# API Endpoints

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    student_id: str = Form(..., description="Student ID"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en', 'es')"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload audio file and transcribe to text
    """
    try:
        logger.info(f"Transcription request from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')} for student {student_id}")
        
        # Validate student access
        student = validate_student_access(student_id, current_user.get("tenant_id"), require_voice=True)
        
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
        print(f"✓ Transcription completed for student {student_id}: '{response.transcript[:50]}...'")
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
        print(f"✓ Text-to-speech generated: {response.filename} ({response.duration:.1f}s, voice: {response.voice_id})")
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
        print(f"✓ Voice list provided: {len(voices)} voices available")
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start new voice conversation session
    """
    try:
        logger.info(f"Conversation start request from {current_user.get('email') or current_user.get('username') or current_user.get('user_id')} for student {request.student_id}")
        
        # Validate student access
        student = validate_student_access(request.student_id, current_user.get("tenant_id"), require_voice=True)
        
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
        print(f"✓ Conversation session started: {session_id} for student {request.student_id}")
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
        student = validate_student_access(conversation['student_id'], current_user.get("tenant_id"), require_voice=True)
        
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
        print(f"✓ Voice message processed: Turn {response.turn_number} - '{response.transcript[:50]}...'")
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
        print(f"✓ Conversation session ended: {session_id} ({conversation['turn_count']} turns)")
        
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
