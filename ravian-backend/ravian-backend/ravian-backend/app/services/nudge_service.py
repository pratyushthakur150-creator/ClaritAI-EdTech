import logging
import uuid
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class NudgeService:
    """Service for sending proactive nudges to students with voice TTS support"""
    
    def __init__(self, db: Session, voice_service=None):
        """
        Initialize NudgeService
        
        Args:
            db: SQLAlchemy database session
            voice_service: Optional voice service for TTS generation
        """
        self.db = db
        self.voice_service = voice_service
        logger.info("NudgeService initialized")
    
    async def send_nudge(
        self,
        student_id: UUID,
        nudge_type: str,
        message: str,
        channel: str,
        tenant_id: UUID,
        voice_settings: dict = None,
        priority: str = "normal"
    ) -> dict:
        """
        Send a proactive nudge to a student
        
        Args:
            student_id: UUID of the target student
            nudge_type: Type of nudge (inactivity_reminder, confusion_help, risk_alert, encouragement)
            message: Text message content (10-500 characters)
            channel: Delivery channel (in_app, email, sms, voice)
            tenant_id: Tenant ID for multi-tenant security
            voice_settings: Optional voice settings for TTS (voice_id, speed)
            priority: Nudge priority (low, normal, high)
            
        Returns:
            dict: Response matching SendNudgeResponse schema
            
        Raises:
            HTTPException: On database or service errors
        """
        try:
            from app.models.student_nudge import StudentNudge
            
            nudge_id = uuid.uuid4()
            audio_url = None
            original_channel = channel
            
            logger.info(f"Sending {nudge_type} nudge to student {student_id} via {channel}")
            
            # Generate audio if voice channel requested
            if channel == "voice" and self.voice_service:
                if not voice_settings:
                    voice_settings = {"voice_id": "nova", "speed": 1.0}
                
                try:
                    logger.debug(f"Generating voice audio for nudge {nudge_id}")
                    audio_result = await self.voice_service.text_to_speech(
                        text=message,
                        voice_id=voice_settings.get("voice_id", "nova"),
                        speed=voice_settings.get("speed", 1.0),
                        tenant_id=tenant_id
                    )
                    
                    audio_url = audio_result.get("audio_url")
                    if audio_url:
                        logger.info(f"✓ Generated voice nudge audio: {audio_url}")
                    else:
                        logger.warning("Voice service returned no audio URL")
                        channel = "in_app"  # Fallback to in_app
                        
                except Exception as e:
                    logger.error(f"✗ Failed to generate voice nudge: {str(e)}")
                    # Fall back to in_app if voice fails
                    channel = "in_app"
                    logger.info(f"Falling back to {channel} delivery")
            
            elif channel == "voice" and not self.voice_service:
                logger.warning("Voice channel requested but no voice service available")
                channel = "in_app"  # Fallback
            
            # Create nudge record in database
            current_time = datetime.now()
            nudge = StudentNudge(
                id=nudge_id,
                tenant_id=tenant_id,
                student_id=student_id,
                nudge_type=nudge_type,
                message=message,
                channel=channel,
                audio_url=audio_url,
                priority=priority,
                status="sent",
                sent_at=current_time
            )
            
            self.db.add(nudge)
            self.db.commit()
            
            # TODO: Implement actual delivery mechanisms
            # - in_app: Already stored in database
            # - email: Integrate with email service
            # - sms: Integrate with SMS service  
            # - voice: Audio URL already generated and stored
            
            success_message = f"Nudge sent successfully via {channel}"
            if original_channel == "voice" and channel == "in_app":
                success_message += " (voice fallback to in_app)"
            
            logger.info(f"✓ Sent {channel} nudge {nudge_id} to student {student_id}")
            
            return {
                "nudge_id": nudge_id,
                "student_id": student_id,
                "nudge_type": nudge_type,
                "channel": channel,
                "audio_url": audio_url,
                "status": "sent",
                "sent_at": current_time,
                "message": success_message
            }
            
        except Exception as e:
            logger.error(f"✗ Error sending nudge to student {student_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send nudge: {str(e)}"
            )
    
    def get_nudge_history(
        self,
        student_id: UUID,
        tenant_id: UUID,
        limit: int = 50
    ) -> dict:
        """
        Get nudge history for a student with multi-tenant filtering
        
        Args:
            student_id: UUID of the student
            tenant_id: Tenant ID for security filtering
            limit: Maximum number of nudges to return (default 50)
            
        Returns:
            dict: Response matching NudgeHistoryResponse schema
            
        Raises:
            HTTPException: On database errors
        """
        try:
            from app.models.student_nudge import StudentNudge
            
            logger.debug(f"Fetching nudge history for student {student_id}")
            
            # Query nudges with multi-tenant security
            nudges = self.db.query(StudentNudge).filter(
                StudentNudge.student_id == student_id,
                StudentNudge.tenant_id == tenant_id
            ).order_by(StudentNudge.sent_at.desc()).limit(limit).all()
            
            # Calculate statistics
            voice_count = sum(1 for n in nudges if n.channel == "voice")
            text_count = len(nudges) - voice_count
            read_count = sum(1 for n in nudges if n.read_at is not None)
            
            logger.info(f"✓ Retrieved {len(nudges)} nudges for student {student_id}")
            
            return {
                "student_id": student_id,
                "nudges": [
                    {
                        "nudge_id": n.id,
                        "nudge_type": n.nudge_type,
                        "message": n.message,
                        "channel": n.channel,
                        "audio_url": n.audio_url,
                        "status": n.status,
                        "sent_at": n.sent_at,
                        "read_at": n.read_at
                    }
                    for n in nudges
                ],
                "total_nudges": len(nudges),
                "voice_nudges": voice_count,
                "text_nudges": text_count,
                "read_count": read_count
            }
            
        except Exception as e:
            logger.error(f"✗ Error fetching nudge history for student {student_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch nudge history: {str(e)}"
            )
    
    async def send_automated_nudges(
        self,
        course_id: UUID,
        tenant_id: UUID
    ) -> dict:
        """
        Send automated nudges based on student risk analysis
        
        This method identifies at-risk students and sends appropriate nudges.
        Typically called by scheduled tasks or cron jobs.
        
        Args:
            course_id: UUID of the course to analyze
            tenant_id: Tenant ID for multi-tenant security
            
        Returns:
            dict: Summary of automated nudges sent
            
        Raises:
            HTTPException: On service errors
        """
        try:
            logger.info(f"Starting automated nudge process for course {course_id}")
            
            from app.services.risk_scoring_service import RiskScoringService
            
            # Get at-risk students using risk scoring service
            risk_service = RiskScoringService(self.db)
            at_risk_data = risk_service.get_at_risk_students(
                course_id=course_id,
                tenant_id=tenant_id,
                min_risk_score=60  # Focus on higher risk students
            )
            
            nudges_sent = 0
            students_processed = at_risk_data.get("students", [])
            
            logger.info(f"Found {len(students_processed)} at-risk students")
            
            # Send nudges to high and critical risk students
            for student in students_processed:
                risk_level = student.get("risk_level", "").lower()
                
                if risk_level in ["high", "critical"]:
                    # Customize message based on risk level
                    if risk_level == "critical":
                        message = f"Hi {student.get('student_name', 'there')}! We noticed you might need urgent support. Your mentor is ready to help you succeed. Let's connect!"
                        priority = "high"
                    else:
                        message = f"Hi {student.get('student_name', 'there')}! We're here to support your learning journey. Your mentor is available whenever you need help!"
                        priority = "normal"
                    
                    try:
                        await self.send_nudge(
                            student_id=student["student_id"],
                            nudge_type="risk_alert",
                            message=message,
                            channel="in_app",
                            tenant_id=tenant_id,
                            priority=priority
                        )
                        nudges_sent += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send nudge to student {student['student_id']}: {e}")
                        continue
            
            summary = {
                "course_id": course_id,
                "students_analyzed": len(students_processed),
                "nudges_sent": nudges_sent,
                "high_risk_count": at_risk_data.get("high_count", 0),
                "critical_risk_count": at_risk_data.get("critical_count", 0),
                "total_at_risk": at_risk_data.get("total_at_risk", 0)
            }
            
            logger.info(f"✓ Automated nudge process complete: {nudges_sent} nudges sent to {len(students_processed)} students")
            
            return summary
            
        except Exception as e:
            logger.error(f"✗ Error in automated nudge process for course {course_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send automated nudges: {str(e)}"
            )
    
    def mark_nudge_as_read(
        self,
        nudge_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        Mark a nudge as read by the student
        
        Args:
            nudge_id: UUID of the nudge to mark as read
            tenant_id: Tenant ID for security filtering
            
        Returns:
            bool: True if successfully marked as read
            
        Raises:
            HTTPException: On database errors or nudge not found
        """
        try:
            from app.models.student_nudge import StudentNudge
            
            nudge = self.db.query(StudentNudge).filter(
                StudentNudge.id == nudge_id,
                StudentNudge.tenant_id == tenant_id
            ).first()
            
            if not nudge:
                raise HTTPException(
                    status_code=404,
                    detail="Nudge not found"
                )
            
            if not nudge.read_at:
                nudge.read_at = datetime.now()
                self.db.commit()
                logger.info(f"✓ Marked nudge {nudge_id} as read")
                return True
            
            return True  # Already read
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"✗ Error marking nudge {nudge_id} as read: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to mark nudge as read: {str(e)}"
            )
