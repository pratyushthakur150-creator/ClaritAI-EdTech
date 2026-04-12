
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import HTTPException

# Import the database models
from app.models.course_module import CourseModule
from app.models.student_interaction import StudentInteraction

# Configure logging
logger = logging.getLogger(__name__)


class HeatmapService:
    """
    Service class for generating course confusion heatmaps.
    
    This service provides functionality to analyze student interactions across course modules
    and generate confusion heatmaps showing areas where students struggle the most.
    The service implements multi-tenant security by filtering all queries on tenant_id.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the HeatmapService with a database session.
        
        Args:
            db (Session): SQLAlchemy database session for executing queries
        """
        self.db = db
        logger.info("HeatmapService initialized")
    
    def get_course_heatmap(self, course_id: UUID, tenant_id: UUID) -> Dict[str, Any]:
        """
        Generate a confusion heatmap for a specific course.
        
        This method analyzes student interactions across course modules to identify
        areas of confusion. It calculates confusion scores based on confidence levels
        and provides detailed metrics for each module.
        
        Args:
            course_id (UUID): The unique identifier of the course
            tenant_id (UUID): The tenant identifier for multi-tenant security
            
        Returns:
            Dict[str, Any]: A dictionary containing heatmap data matching HeatmapResponse schema:
            {
                "course_id": str,
                "modules": [
                    {
                        "module_id": str,
                        "name": str,
                        "confusion_score": float,
                        "interaction_count": int,
                        "top_confused_topics": [str, ...]
                    }
                ],
                "overall_metrics": {
                    "most_confused_module": str,
                    "least_confused_module": str,
                    "average_confusion_score": float,
                    "total_interactions": int
                }
            }
            
        Raises:
            HTTPException: If there's an error processing the heatmap request
        """
        logger.info(f"Generating course heatmap for course_id={course_id}, tenant_id={tenant_id}")
        
        try:
            # Step 1: Get all modules for the course with multi-tenant filtering
            logger.debug("Querying course modules with multi-tenant filtering")
            course_modules = self.db.query(CourseModule).filter(
                CourseModule.course_id == course_id,
                CourseModule.tenant_id == tenant_id
            ).order_by(CourseModule.order_index).all()
            
            # Handle edge case: course has no modules
            if not course_modules:
                logger.info(f"No modules found for course_id={course_id}, returning empty heatmap")
                return {
                    "course_id": str(course_id),
                    "modules": [],
                    "overall_metrics": {
                        "most_confused_module": None,
                        "least_confused_module": None,
                        "average_confusion_score": 0.0,
                        "total_interactions": 0
                    }
                }
            
            logger.debug(f"Found {len(course_modules)} modules for course")
            
            # Step 2: Calculate confusion scores for each module
            module_data = []
            total_interactions = 0
            confusion_scores = []
            
            for module in course_modules:
                logger.debug(f"Processing module: {module.name} (id={module.id})")
                
                # Query student interactions for this module with multi-tenant filtering
                interactions = self.db.query(StudentInteraction).filter(
                    StudentInteraction.module_id == module.id,
                    StudentInteraction.course_id == course_id,
                    StudentInteraction.tenant_id == tenant_id
                ).all()
                
                interaction_count = len(interactions)
                total_interactions += interaction_count
                
                logger.debug(f"Found {interaction_count} interactions for module {module.name}")
                
                if interaction_count > 0:
                    # Calculate confusion score as (1 - avg_confidence) * 100
                    confidences = [i.confidence for i in interactions if i.confidence is not None]
                    
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        confusion_score = (1 - avg_confidence) * 100
                        logger.debug(f"Module {module.name}: avg_confidence={avg_confidence:.3f}, confusion_score={confusion_score:.2f}")
                    else:
                        # No confidence data available, assume moderate confusion
                        confusion_score = 50.0
                        logger.debug(f"Module {module.name}: No confidence data, using default confusion_score=50.0")
                    
                    # Get top confused topics for this module
                    topic_query = self.db.query(
                        StudentInteraction.topic,
                        func.avg(StudentInteraction.confidence).label('avg_confidence'),
                        func.count(StudentInteraction.id).label('interaction_count')
                    ).filter(
                        StudentInteraction.module_id == module.id,
                        StudentInteraction.course_id == course_id,
                        StudentInteraction.tenant_id == tenant_id,
                        StudentInteraction.topic.isnot(None)
                    ).group_by(StudentInteraction.topic).all()
                    
                    # Sort topics by confusion (lowest avg_confidence = highest confusion)
                    confused_topics = []
                    for topic_data in topic_query:
                        if topic_data.avg_confidence is not None:
                            topic_confusion = (1 - topic_data.avg_confidence) * 100
                            confused_topics.append((topic_data.topic, topic_confusion))
                    
                    # Get top 5 most confused topics
                    confused_topics.sort(key=lambda x: x[1], reverse=True)
                    top_confused_topics = [topic[0] for topic in confused_topics[:5]]
                    
                    logger.debug(f"Top confused topics for {module.name}: {top_confused_topics}")
                else:
                    # No interactions for this module
                    confusion_score = 0.0
                    top_confused_topics = []
                    logger.debug(f"Module {module.name}: No interactions, confusion_score=0.0")
                
                confusion_scores.append(confusion_score)
                
                module_data.append({
                    "module_id": str(module.id),
                    "name": module.name,
                    "confusion_score": round(confusion_score, 2),
                    "interaction_count": interaction_count,
                    "top_confused_topics": top_confused_topics
                })
            
            # Step 3: Calculate overall metrics
            logger.debug("Calculating overall metrics")
            
            if confusion_scores:
                average_confusion_score = sum(confusion_scores) / len(confusion_scores)
                
                # Find most and least confused modules
                max_confusion_idx = confusion_scores.index(max(confusion_scores))
                min_confusion_idx = confusion_scores.index(min(confusion_scores))
                
                most_confused_module = course_modules[max_confusion_idx].name
                least_confused_module = course_modules[min_confusion_idx].name
                
                logger.debug(f"Most confused module: {most_confused_module} ({max(confusion_scores):.2f})")
                logger.debug(f"Least confused module: {least_confused_module} ({min(confusion_scores):.2f})")
                logger.debug(f"Average confusion score: {average_confusion_score:.2f}")
            else:
                average_confusion_score = 0.0
                most_confused_module = None
                least_confused_module = None
            
            # Step 4: Build the final heatmap response
            heatmap_response = {
                "course_id": str(course_id),
                "modules": module_data,
                "overall_metrics": {
                    "most_confused_module": most_confused_module,
                    "least_confused_module": least_confused_module,
                    "average_confusion_score": round(average_confusion_score, 2),
                    "total_interactions": total_interactions
                }
            }
            
            logger.info(f"Successfully generated heatmap for course {course_id} with {len(module_data)} modules and {total_interactions} total interactions")
            
            return heatmap_response
            
        except Exception as e:
            logger.error(f"Error generating course heatmap for course_id={course_id}, tenant_id={tenant_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate course heatmap: {str(e)}"
            )


# Utility function to create heatmap service instance
def create_heatmap_service(db: Session) -> HeatmapService:
    """
    Factory function to create a HeatmapService instance.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        HeatmapService: Configured heatmap service instance
    """
    return HeatmapService(db)
