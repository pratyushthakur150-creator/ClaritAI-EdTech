import logging
from typing import List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ConfusionTrackingService:
    """Service to track and analyze student confusion patterns"""
    
    def __init__(self, db: Session):
        self.db = db
        self.confusion_threshold = 0.65  # Confidence below this = confusion
        logger.info("ConfusionTrackingService initialized with confusion threshold: %.2f", self.confusion_threshold)
    
    def get_top_confused_topics(
        self,
        course_id: UUID,
        tenant_id: UUID,
        limit: int = 10,
        days_back: int = 30
    ) -> dict:
        """Get the most confused topics in a course"""
        
        logger.info(f"Getting top confused topics for course {course_id}, tenant {tenant_id}")
        
        try:
            from app.models.student_interaction import StudentInteraction
            
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Query interactions with low confidence (confusion signal)
            # MULTI-TENANT SECURITY: Always filter by tenant_id
            confused_interactions = self.db.query(StudentInteraction).filter(
                and_(
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id,  # Multi-tenant security
                    StudentInteraction.confidence < self.confusion_threshold,
                    StudentInteraction.created_at >= since_date
                )
            ).all()
            
            logger.info(f"Found {len(confused_interactions)} confused interactions")
            
            # Aggregate by topic
            topic_stats = {}
            
            for interaction in confused_interactions:
                topic = interaction.topic or "General"
                
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        "topic": topic,
                        "confusion_count": 0,
                        "students": set(),
                        "confidences": [],
                        "questions": [],
                        "module_id": interaction.module_id
                    }
                
                topic_stats[topic]["confusion_count"] += 1
                topic_stats[topic]["students"].add(str(interaction.student_id))
                topic_stats[topic]["confidences"].append(interaction.confidence)
                
                if len(topic_stats[topic]["questions"]) < 3:
                    topic_stats[topic]["questions"].append(interaction.query)
            
            # Convert to response format
            topics = []
            for topic_data in topic_stats.values():
                avg_confidence = sum(topic_data["confidences"]) / len(topic_data["confidences"]) if topic_data["confidences"] else 0.0
                topics.append({
                    "topic": topic_data["topic"],
                    "confusion_count": topic_data["confusion_count"],
                    "student_count": len(topic_data["students"]),
                    "avg_confidence": avg_confidence,
                    "recent_questions": topic_data["questions"],
                    "module_id": topic_data["module_id"],
                    "module_name": None  # Will be populated by API layer if needed
                })
            
            # Sort by confusion count
            topics.sort(key=lambda x: x["confusion_count"], reverse=True)
            
            result = {
                "course_id": course_id,
                "topics": topics[:limit],
                "total_confusion_signals": len(confused_interactions),
                "date_range": f"Last {days_back} days"
            }
            
            logger.info(f"Returning {len(result['topics'])} top confused topics")
            return result
            
        except Exception as e:
            logger.error(f"Error getting top confused topics: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to retrieve confused topics: {str(e)}"
            )
    
    def get_student_confusion(
        self,
        student_id: UUID,
        course_id: UUID,
        tenant_id: UUID
    ) -> dict:
        """Get confusion patterns for a specific student"""
        
        logger.info(f"Getting confusion patterns for student {student_id} in course {course_id}, tenant {tenant_id}")
        
        try:
            from app.models.student_interaction import StudentInteraction
            
            # Get all interactions for student
            # MULTI-TENANT SECURITY: Always filter by tenant_id
            interactions = self.db.query(StudentInteraction).filter(
                and_(
                    StudentInteraction.student_id == student_id,
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id  # Multi-tenant security
                )
            ).order_by(StudentInteraction.created_at.desc()).all()
            
            logger.info(f"Found {len(interactions)} total interactions for student")
            
            # Group by topic
            topic_patterns = {}
            
            for interaction in interactions:
                topic = interaction.topic or "General"
                
                if topic not in topic_patterns:
                    topic_patterns[topic] = {
                        "topic": topic,
                        "questions": [],
                        "confidences": [],
                        "escalations": 0,
                        "last_asked": interaction.created_at
                    }
                
                topic_patterns[topic]["questions"].append(interaction.query)
                topic_patterns[topic]["confidences"].append(interaction.confidence)
                
                if interaction.escalated_to_mentor:
                    topic_patterns[topic]["escalations"] += 1
                
                if interaction.created_at > topic_patterns[topic]["last_asked"]:
                    topic_patterns[topic]["last_asked"] = interaction.created_at
            
            # Build confusion patterns
            patterns = []
            total_confused = 0
            
            for topic_data in topic_patterns.values():
                if not topic_data["confidences"]:
                    continue
                    
                avg_conf = sum(topic_data["confidences"]) / len(topic_data["confidences"])
                
                # Only include if showing confusion signs
                if avg_conf < self.confusion_threshold or topic_data["escalations"] > 0:
                    patterns.append({
                        "topic": topic_data["topic"],
                        "question_count": len(topic_data["questions"]),
                        "avg_confidence": avg_conf,
                        "last_asked": topic_data["last_asked"],
                        "escalated": topic_data["escalations"] > 0
                    })
                    total_confused += 1
            
            # Determine risk level
            escalated_count = sum(1 for p in patterns if p["escalated"])
            
            if total_confused >= 5 or escalated_count >= 2:
                risk_level = "high"
            elif total_confused >= 2 or escalated_count >= 1:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Sort by question count (most active confusion first)
            patterns.sort(key=lambda x: x["question_count"], reverse=True)
            
            result = {
                "student_id": student_id,
                "course_id": course_id,
                "confusion_patterns": patterns,
                "total_confused_topics": total_confused,
                "risk_level": risk_level
            }
            
            logger.info(f"Student has {total_confused} confused topics with risk level: {risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting student confusion patterns: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve student confusion patterns: {str(e)}"
            )
    
    def analyze_confusion_trends(
        self,
        course_id: UUID,
        tenant_id: UUID,
        days_back: int = 7
    ) -> Dict:
        """Analyze confusion trends over time for dashboard insights"""
        
        logger.info(f"Analyzing confusion trends for course {course_id}, tenant {tenant_id}")
        
        try:
            from app.models.student_interaction import StudentInteraction
            
            since_date = datetime.now() - timedelta(days=days_back)
            
            # MULTI-TENANT SECURITY: Always filter by tenant_id
            interactions = self.db.query(StudentInteraction).filter(
                and_(
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id,  # Multi-tenant security
                    StudentInteraction.created_at >= since_date
                )
            ).all()
            
            # Analyze trends
            total_interactions = len(interactions)
            confused_interactions = [i for i in interactions if i.confidence < self.confusion_threshold]
            confusion_rate = len(confused_interactions) / total_interactions if total_interactions > 0 else 0
            
            escalated_interactions = [i for i in interactions if i.escalated_to_mentor]
            escalation_rate = len(escalated_interactions) / total_interactions if total_interactions > 0 else 0
            
            avg_confidence = sum(i.confidence for i in interactions) / total_interactions if total_interactions > 0 else 0
            
            result = {
                "total_interactions": total_interactions,
                "confusion_rate": confusion_rate,
                "escalation_rate": escalation_rate,
                "avg_confidence": avg_confidence,
                "confused_interactions": len(confused_interactions),
                "escalated_interactions": len(escalated_interactions),
                "analysis_period_days": days_back
            }
            
            logger.info(f"Confusion analysis complete: {confusion_rate:.2%} confusion rate")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing confusion trends: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze confusion trends: {str(e)}"
            )
