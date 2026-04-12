# Assistant Router with Voice Support

# Assistant Router with Voice Support

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import subprocess

try:
    from fastapi import APIRouter, Depends, HTTPException, status, Query, Path as FastAPIPath
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
except ImportError:
    raise
    from fastapi import APIRouter, Depends, HTTPException, status, Query, Path as FastAPIPath
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    raise
    from pydantic import BaseModel, Field, field_validator

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

# Initialize router and security
router = APIRouter(tags=["assistant"])
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'demo-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

print("✓ All dependencies installed successfully")

# Mock services for demo purposes
class MockStudent:
    def __init__(self, student_id: str, tenant_id: str, name: str, voice_enabled: bool = True):
        self.id = student_id
        self.tenant_id = tenant_id
        self.name = name
        self.voice_enabled = voice_enabled

class MockAssistantService:
    def __init__(self):
        self.demo_mode = True
        self.interaction_logs = []

    async def answer_query(self, student, tenant_id: str, query: str = None, audio_url: str = None,
                          mode: str = 'text', voice_settings: Dict = None, return_audio: bool = True) -> Dict:
        """Mock implementation of AssistantService.answer_query"""
        import uuid
        
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Generate mock response based on query content
        if query and "machine learning" in query.lower():
            answer = ("Machine learning is a subset of artificial intelligence that enables computers to learn "
                     "and make decisions from data without being explicitly programmed. It involves algorithms "
                     "that can identify patterns, make predictions, and improve performance through experience.")
            sources = [
                {"id": "ml_basics_001", "content": "Introduction to Machine Learning concepts", "relevance_score": 0.92, "metadata": {"type": "textbook", "chapter": 1}},
                {"id": "ml_algorithms_002", "content": "Common ML algorithms and their applications", "relevance_score": 0.87, "metadata": {"type": "article", "topic": "algorithms"}}
            ]
            follow_ups = [
                "What are the main types of machine learning?",
                "Can you give examples of supervised learning?",
                "How do I choose the right ML algorithm?"
            ]
            confidence = 0.91
        elif query and "python" in query.lower():
            answer = ("Python is a high-level, interpreted programming language known for its simplicity and "
                     "readability. It's widely used in data science, web development, automation, and machine learning "
                     "due to its extensive library ecosystem and ease of learning.")
            sources = [
                {"id": "python_intro_001", "content": "Python programming fundamentals", "relevance_score": 0.89, "metadata": {"type": "tutorial", "difficulty": "beginner"}}
            ]
            follow_ups = [
                "How do I install Python libraries?",
                "What are Python's main advantages?",
                "What projects can I build with Python?"
            ]
            confidence = 0.88
        else:
            answer = ("I can help you with your question. Based on the available information, "
                     "let me provide you with a comprehensive answer tailored to your learning needs.")
            sources = [
                {"id": "general_001", "content": "General educational content", "relevance_score": 0.75, "metadata": {"type": "reference"}}
            ]
            follow_ups = [
                "Can you explain this in more detail?",
                "What are some practical examples?",
                "How does this relate to my coursework?"
            ]
            confidence = 0.76

        # Mock response structure
        response = {
            'interaction_id': interaction_id,
            'timestamp': timestamp,
            'student_id': student.id,
            'tenant_id': tenant_id,
            'mode': mode,
            'query_text': query or "Demo query from audio",
            'answer_text': answer,
            'sources': sources,
            'follow_up_questions': follow_ups,
            'confidence_score': confidence,
            'escalation': {
                'needed': confidence < 0.8,
                'reason': 'Low confidence response' if confidence < 0.8 else None,
                'confidence_score': confidence,
                'context_relevance': 0.85
            },
            'processing_time': 1.2
        }
        
        # Add voice-specific fields if in voice mode
        if mode == 'voice':
            response.update({
                'audio_url': audio_url,
                'transcript': query or "What is machine learning and how does it work?",
                'audio_duration': 4.5,
                'response_audio_url': f"/api/v1/voice/audio/{tenant_id}/response_{interaction_id[:8]}.mp3" if return_audio else None,
                'response_audio_duration': len(answer) / 12.0 if return_audio else None
            })
        
        # Store interaction for history
        self.interaction_logs.append(response.copy())
        
        return response
    
    def get_interaction_history(self, student_id: str, tenant_id: str, limit: int = 10) -> List[Dict]:
        """Get interaction history for a student"""
        student_interactions = [
            log for log in self.interaction_logs 
            if log.get('student_id') == student_id and log.get('tenant_id') == tenant_id
        ]
        return sorted(student_interactions, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]

# Mock data
mock_students = {
    'student_1': MockStudent('student_1', 'tenant_123', 'John Doe', voice_enabled=True),
    'student_2': MockStudent('student_2', 'tenant_456', 'Jane Smith', voice_enabled=True),
    'student_3': MockStudent('student_3', 'tenant_123', 'Bob Wilson', voice_enabled=False),
}

# Mock feedback storage
feedback_storage = []

# Initialize services
assistant_service = MockAssistantService()

# --- Pydantic Models ---

class VoiceSettings(BaseModel):
    """Voice synthesis settings"""
    voice_id: str = Field(default='alloy', description="Voice ID for TTS")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")
    return_audio: bool = Field(default=True, description="Whether to return audio response")
    
    @field_validator('voice_id')
    def validate_voice_id(cls, v):
        allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        if v not in allowed_voices:
            raise ValueError(f'Voice ID must be one of: {allowed_voices}')
        return v

class QueryContext(BaseModel):
    """Context information for the query"""
    module_id: Optional[str] = Field(None, description="Current module ID")
    lesson_id: Optional[str] = Field(None, description="Current lesson ID")
    timestamp: Optional[str] = Field(None, description="Query timestamp")
    session_id: Optional[str] = Field(None, description="Learning session ID")

class AssistantQueryRequest(BaseModel):
    """Request model for assistant queries supporting both text and voice modes"""
    student_id: str = Field(..., description="Student ID making the query")
    mode: str = Field(..., description="Query mode: 'text' or 'voice'")
    
    # Text mode parameters
    query: Optional[str] = Field(None, description="Text question (required for text mode)")
    
    # Voice mode parameters
    audio_url: Optional[str] = Field(None, description="Audio file URL (required for voice mode)")
    
    # Optional parameters for both modes
    voice_settings: Optional[VoiceSettings] = Field(None, description="Voice synthesis settings")
    context: Optional[QueryContext] = Field(None, description="Query context information")
    
    @field_validator('mode')
    def validate_mode(cls, v):
        if v not in ['text', 'voice']:
            raise ValueError("Mode must be 'text' or 'voice'")
        return v
    
    def validate_mode_requirements(self):
        """Validate required parameters based on mode"""
        if self.mode == 'text' and not self.query:
            raise ValueError("query parameter is required for text mode")
        elif self.mode == 'voice' and not self.audio_url:
            raise ValueError("audio_url parameter is required for voice mode")

class Source(BaseModel):
    """Source information from RAG search"""
    id: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any] = {}

class EscalationInfo(BaseModel):
    """Escalation information"""
    needed: bool
    reason: Optional[str]
    confidence_score: float
    context_relevance: float

class AssistantQueryResponse(BaseModel):
    """Response model for assistant queries"""
    interaction_id: str
    timestamp: str
    student_id: str
    tenant_id: str
    mode: str
    
    # Core response fields
    answer_text: str
    confidence_score: float
    sources: List[Source]
    follow_up_questions: List[str]
    escalation: EscalationInfo
    processing_time: float
    
    # Query-specific fields
    query_text: str
    
    # Voice mode specific fields (optional)
    transcript: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    response_audio_url: Optional[str] = None
    response_audio_duration: Optional[float] = None

class InteractionHistory(BaseModel):
    """Historical interaction record"""
    interaction_id: str
    timestamp: str
    mode: str
    query_text: str
    answer_text: str
    confidence_score: float
    escalation_needed: bool
    audio_duration: Optional[float] = None

class HistoryResponse(BaseModel):
    """Response model for interaction history"""
    student_id: str
    tenant_id: str
    total_interactions: int
    interactions: List[InteractionHistory]
    request_timestamp: str

class FeedbackRequest(BaseModel):
    """Request model for interaction feedback"""
    interaction_id: str = Field(..., description="ID of the interaction being rated")
    student_id: str = Field(..., description="Student providing feedback")
    feedback_text: Optional[str] = Field(None, description="Written feedback")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5")
    helpful: Optional[bool] = Field(None, description="Was the response helpful?")
    
    # Voice-specific feedback
    voice_clarity: Optional[int] = Field(None, ge=1, le=5, description="Voice clarity rating")
    voice_speed: Optional[int] = Field(None, ge=1, le=5, description="Voice speed rating")
    
    @field_validator('rating', 'voice_clarity', 'voice_speed')
    def validate_ratings(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    feedback_id: str
    interaction_id: str
    student_id: str
    tenant_id: str
    timestamp: str
    status: str

# --- Authentication and Validation ---

def validate_student_access(student_id: str, tenant_id: str, require_voice: bool = False) -> MockStudent:
    """Validate student access and permissions"""
    student = mock_students.get(student_id)
    if not student:
        logger.warning(f"Student not found: {student_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    if student.tenant_id != tenant_id:
        logger.warning(f"Tenant mismatch for student {student_id}: {student.tenant_id} != {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: student not in your tenant"
        )
    
    if require_voice and not student.voice_enabled:
        logger.warning(f"Voice not enabled for student {student_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voice features not enabled for this student"
        )
    
    logger.info(f"Student access validated: {student_id} in tenant {tenant_id}")
    return student

# --- API Endpoints ---

@router.post("/query", response_model=AssistantQueryResponse)
async def query_assistant(
    request: AssistantQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Query the AI assistant with text or voice input.

    **Text Mode:**
    - Provide query text directly
    - Get text response with sources and follow-ups
    - Optional voice synthesis of response

    **Voice Mode:**
    - Provide audio_url pointing to uploaded audio
    - Get transcription, text answer, and optional voice response
    - Includes audio duration and transcript information

    **Features:**
    - Multi-tenant security validation
    - RAG-enhanced responses with source citations
    - Confidence scoring and escalation detection
    - Follow-up question suggestions
    - Comprehensive interaction logging
    """
    try:
        username = current_user.get("email") or current_user.get("username") or current_user.get("user_id")
        tenant_id = current_user.get("tenant_id")
        logger.info(f"Assistant query from {username} for student {request.student_id} in {request.mode} mode")
        
        # Validate mode-specific requirements
        request.validate_mode_requirements()
        
        # Validate student access
        student = validate_student_access(
            request.student_id,
            tenant_id,
            require_voice=(request.mode == 'voice')
        )
        
        # Prepare parameters for AssistantService
        service_params = {
            'student': student,
            'tenant_id': tenant_id,
            'mode': request.mode
        }
        
        # Add mode-specific parameters
        if request.mode == 'text':
            service_params['query'] = request.query
        elif request.mode == 'voice':
            service_params['audio_url'] = request.audio_url
        
        # Add voice settings if provided
        if request.voice_settings:
            service_params['voice_settings'] = request.voice_settings.dict()
            service_params['return_audio'] = request.voice_settings.return_audio
        else:
            service_params['voice_settings'] = {}
            service_params['return_audio'] = request.mode == 'voice'
        
        logger.info(f"Calling AssistantService.answer_query with mode: {request.mode}")
        
        # Call AssistantService
        assistant_response = await assistant_service.answer_query(**service_params)
        
        # Map escalation info
        escalation_data = assistant_response.get('escalation', {})
        escalation = EscalationInfo(
            needed=escalation_data.get('needed', False),
            reason=escalation_data.get('reason'),
            confidence_score=escalation_data.get('confidence_score', assistant_response.get('confidence_score', 0.0)),
            context_relevance=escalation_data.get('context_relevance', 0.0)
        )
        
        # Map sources
        sources = [
            Source(
                id=source.get('id', ''),
                content=source.get('content', ''),
                relevance_score=source.get('relevance_score', 0.0),
                metadata=source.get('metadata', {})
            )
            for source in assistant_response.get('sources', [])
        ]
        
        # Create response
        response = AssistantQueryResponse(
            interaction_id=assistant_response['interaction_id'],
            timestamp=assistant_response['timestamp'],
            student_id=assistant_response['student_id'],
            tenant_id=assistant_response['tenant_id'],
            mode=assistant_response['mode'],
            query_text=assistant_response['query_text'],
            answer_text=assistant_response['answer_text'],
            confidence_score=assistant_response['confidence_score'],
            sources=sources,
            follow_up_questions=assistant_response.get('follow_up_questions', []),
            escalation=escalation,
            processing_time=assistant_response.get('processing_time', 0.0)
        )
        
        # Add voice-specific fields if available
        if request.mode == 'voice':
            response.transcript = assistant_response.get('transcript')
            response.audio_url = assistant_response.get('audio_url')
            response.audio_duration = assistant_response.get('audio_duration')
            response.response_audio_url = assistant_response.get('response_audio_url')
            response.response_audio_duration = assistant_response.get('response_audio_duration')
        
        logger.info(f"Query processed successfully: {response.interaction_id} (confidence: {response.confidence_score:.2f})")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assistant query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant query processing failed: {str(e)}"
        )

@router.get("/history/{student_id}", response_model=HistoryResponse)
async def get_student_history(
    student_id: str = FastAPIPath(..., description="Student ID to get history for"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of interactions to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get interaction history for a student including both text and voice interactions.

    **Features:**
    - Multi-tenant filtered results
    - Pagination with configurable limit
    - Includes voice interaction metadata
    - Sorted by most recent first
    - Audio duration tracking for voice interactions
    """
    try:
        username = current_user.get("email") or current_user.get("username") or current_user.get("user_id")
        tenant_id = current_user.get("tenant_id")
        logger.info(f"History request for student {student_id} from {username}")

        # Validate student access
        student = validate_student_access(student_id, tenant_id)
        
        # Get interaction history
        history_data = assistant_service.get_interaction_history(student_id, current_user.tenant_id, limit)
        
        # Map to response format
        interactions = [
            InteractionHistory(
                interaction_id=interaction['interaction_id'],
                timestamp=interaction['timestamp'],
                mode=interaction['mode'],
                query_text=interaction['query_text'],
                answer_text=interaction['answer_text'],
                confidence_score=interaction['confidence_score'],
                escalation_needed=interaction.get('escalation', {}).get('needed', False),
                audio_duration=interaction.get('audio_duration')
            )
            for interaction in history_data
        ]
        
        response = HistoryResponse(
            student_id=student_id,
            tenant_id=tenant_id,
            total_interactions=len(interactions),
            interactions=interactions,
            request_timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"History retrieved: {len(interactions)} interactions for student {student_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interaction history: {str(e)}"
        )

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback on a previous assistant interaction.

    **Features:**
    - Rate overall helpfulness and accuracy
    - Voice-specific feedback (clarity, speed)
    - Written feedback comments
    - Multi-tenant security validation
    - Feedback tracking and analytics
    """
    try:
        username = current_user.get("email") or current_user.get("username") or current_user.get("user_id")
        tenant_id = current_user.get("tenant_id")
        logger.info(f"Feedback submission for interaction {feedback.interaction_id} from {username}")

        # Validate student access
        student = validate_student_access(feedback.student_id, tenant_id)
        
        # Create feedback record
        import uuid
        feedback_id = str(uuid.uuid4())
        feedback_record = {
            'feedback_id': feedback_id,
            'interaction_id': feedback.interaction_id,
            'student_id': feedback.student_id,
            'tenant_id': tenant_id,
            'timestamp': datetime.now().isoformat(),
            'feedback_text': feedback.feedback_text,
            'rating': feedback.rating,
            'helpful': feedback.helpful,
            'voice_clarity': feedback.voice_clarity,
            'voice_speed': feedback.voice_speed,
            'submitted_by': username
        }
        
        # Store feedback
        feedback_storage.append(feedback_record)
        
        response = FeedbackResponse(
            feedback_id=feedback_id,
            interaction_id=feedback.interaction_id,
            student_id=feedback.student_id,
            tenant_id=current_user.tenant_id,
            timestamp=feedback_record['timestamp'],
            status='submitted'
        )
        
        logger.info(f"Feedback submitted successfully: {feedback_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the assistant service.
    
    Returns service status, available endpoints, and configuration information.
    """
    return {
        "status": "healthy",
        "service": "assistant",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "text_mode": True,
            "voice_mode": True,
            "rag_search": True,
            "multi_tenant": True,
            "interaction_history": True,
            "feedback_collection": True
        },
        "endpoints": [
            "POST /query",
            "GET /history/{student_id}",
            "POST /feedback",
            "GET /health"
        ],
        "demo_mode": assistant_service.demo_mode
    }
