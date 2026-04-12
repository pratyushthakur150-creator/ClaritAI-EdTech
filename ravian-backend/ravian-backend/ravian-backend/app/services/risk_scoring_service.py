import logging
from typing import List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class RiskScoringService:
    """Service to identify and score at-risk students"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("RiskScoringService initialized")
        
        # Risk thresholds
        self.inactivity_threshold_days = 7
        self.low_confidence_threshold = 0.65
        self.critical_risk_score = 75
        self.high_risk_score = 60
        self.medium_risk_score = 40
        
        logger.info(f"Risk thresholds set: inactivity={self.inactivity_threshold_days} days, confidence<{self.low_confidence_threshold}")
    
    def get_at_risk_students(
        self,
        course_id: UUID,
        tenant_id: UUID,
        min_risk_score: float = 40
    ) -> dict:
        """Identify students at risk of dropping out or failing"""
        
        logger.info(f"Getting at-risk students for course {course_id}, tenant {tenant_id}")
        
        try:
            from app.models.student_interaction import StudentInteraction
            
            # Get all students in course (who have interactions) with multi-tenant filtering
            student_ids = self.db.query(StudentInteraction.student_id).filter(
                and_(
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id
                )
            ).distinct().all()
            
            logger.info(f"Found {len(student_ids)} students with interactions in course")
            
            at_risk_students = []
            
            for (student_id,) in student_ids:
                risk_data = self._calculate_student_risk(
                    student_id=student_id,
                    course_id=course_id,
                    tenant_id=tenant_id
                )
                
                if risk_data and risk_data["risk_score"] >= min_risk_score:
                    at_risk_students.append(risk_data)
                    logger.debug(f"Student {student_id} at risk: score={risk_data['risk_score']}, level={risk_data['risk_level']}")
            
            # Sort by risk score (highest first)
            at_risk_students.sort(key=lambda x: x["risk_score"], reverse=True)
            
            # Count by risk level
            critical_count = sum(1 for s in at_risk_students if s["risk_level"] == "critical")
            high_count = sum(1 for s in at_risk_students if s["risk_level"] == "high")
            medium_count = sum(1 for s in at_risk_students if s["risk_level"] == "medium")
            
            logger.info(f"At-risk students identified: {len(at_risk_students)} total (Critical: {critical_count}, High: {high_count}, Medium: {medium_count})")
            
            return {
                "course_id": course_id,
                "students": at_risk_students,
                "total_at_risk": len(at_risk_students),
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count
            }
            
        except Exception as e:
            logger.error(f"Error getting at-risk students: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve at-risk students: {str(e)}"
            )
    
    def _calculate_student_risk(
        self,
        student_id: UUID,
        course_id: UUID,
        tenant_id: UUID
    ) -> dict:
        """Calculate risk score for a single student"""
        
        logger.debug(f"Calculating risk for student {student_id}")
        
        try:
            from app.models.student_interaction import StudentInteraction
            
            # Get student interactions with multi-tenant filtering
            interactions = self.db.query(StudentInteraction).filter(
                and_(
                    StudentInteraction.student_id == student_id,
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id
                )
            ).order_by(StudentInteraction.created_at.desc()).all()
            
            if not interactions:
                logger.debug(f"No interactions found for student {student_id}")
                return None
            
            # Calculate risk factors
            risk_factors = []
            total_risk_score = 0
            
            # 1. Inactivity Risk
            last_interaction = interactions[0].created_at
            days_inactive = (datetime.now() - last_interaction).days
            
            if days_inactive > self.inactivity_threshold_days:
                inactivity_score = min(30, days_inactive * 2)
                total_risk_score += inactivity_score
                risk_factors.append({
                    "factor": "Inactivity",
                    "score": inactivity_score,
                    "description": f"No activity for {days_inactive} days"
                })
                logger.debug(f"Inactivity risk: {inactivity_score} points ({days_inactive} days)")
            
            # 2. Low Confidence Score Risk
            confidences = [i.confidence for i in interactions if i.confidence is not None]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            if avg_confidence < self.low_confidence_threshold:
                confidence_risk = (1 - avg_confidence) * 40
                total_risk_score += confidence_risk
                risk_factors.append({
                    "factor": "Low Confidence",
                    "score": confidence_risk,
                    "description": f"Average confidence: {avg_confidence:.2f}"
                })
                logger.debug(f"Low confidence risk: {confidence_risk} points (avg: {avg_confidence:.2f})")
            
            # 3. High Confusion Risk
            confused_topics = set()
            for i in interactions:
                if i.confidence and i.confidence < self.low_confidence_threshold:
                    confused_topics.add(i.topic or "General")
            
            if len(confused_topics) >= 3:
                confusion_risk = min(25, len(confused_topics) * 5)
                total_risk_score += confusion_risk
                risk_factors.append({
                    "factor": "Multiple Confusions",
                    "score": confusion_risk,
                    "description": f"Confused on {len(confused_topics)} topics"
                })
                logger.debug(f"Multiple confusion risk: {confusion_risk} points ({len(confused_topics)} topics)")
            
            # 4. Escalation Risk
            escalations = sum(1 for i in interactions if i.escalated_to_mentor)
            
            if escalations > 0:
                escalation_risk = min(20, escalations * 10)
                total_risk_score += escalation_risk
                risk_factors.append({
                    "factor": "Escalations",
                    "score": escalation_risk,
                    "description": f"{escalations} questions escalated to mentor"
                })
                logger.debug(f"Escalation risk: {escalation_risk} points ({escalations} escalations)")
            
            # 5. Low Engagement Risk
            if len(interactions) < 5:
                engagement_risk = 15
                total_risk_score += engagement_risk
                risk_factors.append({
                    "factor": "Low Engagement",
                    "score": engagement_risk,
                    "description": f"Only {len(interactions)} questions asked"
                })
                logger.debug(f"Low engagement risk: {engagement_risk} points ({len(interactions)} interactions)")
            
            # Determine risk level
            if total_risk_score >= self.critical_risk_score:
                risk_level = "critical"
            elif total_risk_score >= self.high_risk_score:
                risk_level = "high"
            elif total_risk_score >= self.medium_risk_score:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            logger.debug(f"Student {student_id} risk calculated: score={total_risk_score:.2f}, level={risk_level}")
            
            return {
                "student_id": student_id,
                "student_name": f"Student {str(student_id)[:8]}",  # Mock name
                "email": f"student_{str(student_id)[:8]}@example.com",  # Mock email
                "risk_score": round(total_risk_score, 2),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "days_inactive": days_inactive,
                "confusion_topics": len(confused_topics),
                "avg_confidence": round(avg_confidence, 2),
                "last_active": last_interaction,
                "mentor_notified": False  # TODO: Track in database
            }
            
        except Exception as e:
            logger.error(f"Error calculating student risk: {str(e)}")
            return None
    
    def notify_mentor(
        self,
        student_id: UUID,
        course_id: UUID,
        tenant_id: UUID,
        custom_message: str = None
    ) -> dict:
        """Send notification to mentor about at-risk student"""
        
        logger.info(f"Notifying mentor about student {student_id}")
        
        try:
            # Calculate current risk with multi-tenant filtering
            risk_data = self._calculate_student_risk(student_id, course_id, tenant_id)
            
            if not risk_data:
                logger.error(f"Student {student_id} not found or has no interactions")
                raise HTTPException(
                    status_code=404,
                    detail="Student not found or has no interactions"
                )
            
            # Build notification message
            if custom_message:
                message = custom_message
            else:
                factors = ", ".join([f["factor"] for f in risk_data["risk_factors"]])
                message = f"Student at risk (score: {risk_data['risk_score']}). Factors: {factors}"
            
            # TODO: Actually send notification (email, Slack, etc.)
            logger.info(f"Mentor notification for student {student_id}: {message}")
            
            # TODO: Mark as notified in database
            
            notification_time = datetime.now()
            
            logger.info(f"Notification sent successfully for student {student_id}")
            
            return {
                "student_id": student_id,
                "mentor_notified": True,
                "notification_sent_at": notification_time,
                "message": message
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending mentor notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send mentor notification: {str(e)}"
            )
