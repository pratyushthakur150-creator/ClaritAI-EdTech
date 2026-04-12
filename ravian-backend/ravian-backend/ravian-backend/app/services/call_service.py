"""
Call Service Module

Provides comprehensive call management functionality including:
- Call log creation and management
- Outbound call triggering with Redis queuing
- Sentiment analysis using keyword-based approach
- Cost calculation based on call duration
- Multi-tenant security enforcement
- Analytics event logging
"""

import math
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from redis import Redis

# Import schemas (assuming they exist)
from app.schemas.call import CallLogCreate, CallLogResponse, TriggerCallRequest
from app.schemas.lead import LeadResponse

# Import models (assuming they exist)
from app.models.call import CallLog, CallDirection, SentimentScore
from app.models.lead import Lead
from app.models.analytics import AnalyticsEvent, EventType

# Import custom exceptions (assuming they exist)
class LeadNotFoundError(Exception):
    """Raised when lead is not found or access is denied"""
    pass

class CallNotFoundError(Exception):
    """Raised when call is not found or access is denied"""
    pass

class InvalidCallDataError(Exception):
    """Raised when call data validation fails"""
    pass

class CallService:
    """
    Service class for managing call operations with multi-tenant security
    """
    
    def __init__(self, db: Session, redis_client: Optional[Redis] = None, tenant_id: Optional[UUID] = None):
        """
        Initialize CallService with database session, Redis client, and tenant context
        
        Args:
            db: SQLAlchemy database session
            redis_client: Redis client for queue operations
            tenant_id: Current tenant ID for multi-tenant isolation
        """
        self.db = db
        self.redis_client = redis_client
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(__name__)
        
        # Sentiment analysis keywords
        self.positive_keywords = [
            "yes", "interested", "sounds good", "great", "perfect", "definitely",
            "awesome", "excellent", "wonderful", "amazing", "fantastic", "love it",
            "absolutely", "certainly", "sure", "of course", "that works", "let's do it"
        ]
        
        self.negative_keywords = [
            "not interested", "no", "don't call", "busy", "not now", "remove",
            "unsubscribe", "stop calling", "not available", "can't", "won't",
            "terrible", "awful", "hate", "disgusted", "angry", "frustrated"
        ]
    
    def create_call_log(self, call_data: CallLogCreate, user_id: Optional[UUID] = None) -> CallLogResponse:
        """
        Create a new call log entry with validation and analytics
        
        Args:
            call_data: Call log creation data
            user_id: ID of user creating the call log
            
        Returns:
            CallLogResponse: Created call log with lead information
            
        Raises:
            LeadNotFoundError: If lead doesn't exist or belongs to different tenant
            InvalidCallDataError: If call data is invalid
        """
        try:
            self.logger.info(f"Creating call log for lead {call_data.lead_id} by user {user_id}")
            
            # Validate lead exists and belongs to tenant
            lead = self.db.query(Lead).filter(
                and_(Lead.id == call_data.lead_id, Lead.tenant_id == self.tenant_id)
            ).first()
            
            if not lead:
                self.logger.error(f"Lead {call_data.lead_id} not found for tenant {self.tenant_id}")
                raise LeadNotFoundError(f"Lead {call_data.lead_id} not found")
            
            # Validate call direction
            if call_data.call_direction not in ["INBOUND", "OUTBOUND"]:
                raise InvalidCallDataError(f"Invalid call direction: {call_data.call_direction}")
            
            # Calculate cost based on duration
            cost = self.calculate_cost(call_data.duration)
            
            # Analyze sentiment from transcript if provided
            sentiment = call_data.sentiment
            if not sentiment and call_data.transcript:
                sentiment = self.analyze_sentiment(call_data.transcript)
            
            # Create call log record
            call_log = CallLog(
                lead_id=call_data.lead_id,
                call_direction=call_data.call_direction,
                duration=call_data.duration,
                transcript=call_data.transcript,
                summary=call_data.summary,
                sentiment=sentiment or SentimentScore.NEUTRAL.value,
                outcome=call_data.outcome,
                recording_url=call_data.recording_url,
                cost=cost,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(call_log)
            self.db.flush()  # Get the ID
            
            # Log analytics event
            self._log_analytics_event(
                event_type=EventType.CALL_COMPLETED.value,
                entity_type="call",
                entity_id=call_log.id,
                metadata={
                    "lead_id": str(call_data.lead_id),
                    "call_direction": call_data.call_direction,
                    "duration": call_data.duration,
                    "sentiment": sentiment,
                    "outcome": call_data.outcome,
                    "cost": cost
                },
                user_id=user_id
            )
            
            self.db.commit()
            
            # Create response
            response_data = {
                "id": call_log.id,
                "lead_id": call_log.lead_id,
                "lead_name": lead.name,
                "call_direction": call_log.call_direction,
                "duration": call_log.duration,
                "transcript": call_log.transcript,
                "summary": call_log.summary,
                "sentiment": call_log.sentiment,
                "outcome": call_log.outcome,
                "recording_url": call_log.recording_url,
                "cost": call_log.cost,
                "created_at": call_log.created_at,
                "updated_at": call_log.updated_at
            }
            
            self.logger.info(f"✓ Created call log {call_log.id} for lead {call_data.lead_id}")
            return CallLogResponse(**response_data)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create call log: {str(e)}")
            raise
    
    def trigger_outbound_call(self, request: TriggerCallRequest, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Trigger an outbound call by adding to Redis queue
        
        Args:
            request: Outbound call trigger request
            user_id: ID of user triggering the call
            
        Returns:
            Dict with queue position and estimated call time
            
        Raises:
            LeadNotFoundError: If lead doesn't exist or belongs to different tenant
        """
        try:
            self.logger.info(f"Triggering outbound call for lead {request.lead_id}")
            
            # Validate lead exists and belongs to tenant
            lead = self.db.query(Lead).filter(
                and_(Lead.id == request.lead_id, Lead.tenant_id == self.tenant_id)
            ).first()
            
            if not lead:
                self.logger.error(f"Lead {request.lead_id} not found for tenant {self.tenant_id}")
                raise LeadNotFoundError(f"Lead {request.lead_id} not found")
            
            # Determine queue based on priority
            priority = getattr(request, 'priority', 'warm')
            queue_name = f"call_queue:{priority}"
            
            # Prepare lead context for call
            lead_context = {
                "lead_id": str(request.lead_id),
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "source": lead.source,
                "interested_courses": lead.interested_courses or [],
                "intent": lead.intent,
                "urgency": lead.urgency,
                "chatbot_context": lead.chatbot_context or {},
                "scheduled_at": request.scheduled_at.isoformat() if request.scheduled_at else None,
                "tenant_id": str(self.tenant_id),
                "triggered_by": str(user_id) if user_id else None,
                "triggered_at": datetime.utcnow().isoformat()
            }
            
            # Add to Redis queue if available
            queue_position = 0
            estimated_wait_time = 0
            
            if self.redis_client:
                try:
                    # Add to queue
                    queue_position = self.redis_client.lpush(queue_name, json.dumps(lead_context))
                    
                    # Calculate estimated wait time (assume 5 minutes per call)
                    estimated_wait_time = (queue_position - 1) * 5
                    
                    self.logger.info(f"Added call to {queue_name} at position {queue_position}")
                    
                except Exception as redis_error:
                    self.logger.warning(f"Redis queue operation failed: {redis_error}")
                    # Continue without Redis - call can still be logged
            
            # Create call log record with status "queued"
            call_log = CallLog(
                lead_id=request.lead_id,
                call_direction=CallDirection.OUTBOUND.value,
                duration=0,  # Will be updated when call is completed
                transcript="",
                summary="",
                sentiment=SentimentScore.NEUTRAL.value,
                outcome="queued",
                recording_url="",
                cost=0.0,  # Will be calculated when call is completed
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(call_log)
            self.db.flush()
            
            # Log analytics event
            self._log_analytics_event(
                event_type=EventType.CALL_TRIGGERED.value,
                entity_type="call",
                entity_id=call_log.id,
                metadata={
                    "lead_id": str(request.lead_id),
                    "priority": priority,
                    "queue_position": queue_position,
                    "estimated_wait_time": estimated_wait_time,
                    "scheduled_at": request.scheduled_at.isoformat() if request.scheduled_at else None
                },
                user_id=user_id
            )
            
            self.db.commit()
            
            response = {
                "call_id": call_log.id,
                "lead_id": request.lead_id,
                "lead_name": lead.name,
                "priority": priority,
                "queue_name": queue_name,
                "queue_position": queue_position,
                "estimated_wait_time_minutes": estimated_wait_time,
                "scheduled_at": request.scheduled_at,
                "status": "queued"
            }
            
            self.logger.info(f"✓ Triggered outbound call for lead {request.lead_id}")
            return response
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to trigger outbound call: {str(e)}")
            raise
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text using keyword-based approach
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment category: "positive", "negative", or "neutral"
        """
        if not text:
            return SentimentScore.NEUTRAL.value
        
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        if positive_count > negative_count:
            return SentimentScore.POSITIVE.value
        elif negative_count > positive_count:
            return SentimentScore.NEGATIVE.value
        else:
            return SentimentScore.NEUTRAL.value
    
    def calculate_cost(self, duration_seconds: int) -> float:
        """
        Calculate call cost based on duration
        
        Args:
            duration_seconds: Call duration in seconds
            
        Returns:
            Cost in credits (1 minute = 2 credits)
        """
        if duration_seconds <= 0:
            return 0.0
        
        # Calculate cost: 1 minute = 2 credits, round up partial minutes
        minutes = math.ceil(duration_seconds / 60)
        cost = minutes * 2.0
        
        return cost
    
    def get_calls(
        self,
        sentiment: Optional[str] = None,
        outcome: Optional[str] = None,
        call_direction: Optional[str] = None,
        lead_id: Optional[UUID] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get calls with filtering and pagination
        
        Args:
            sentiment: Filter by sentiment
            outcome: Filter by outcome
            call_direction: Filter by call direction
            lead_id: Filter by specific lead
            created_after: Filter calls created after this datetime
            created_before: Filter calls created before this datetime
            page: Page number (1-based)
            limit: Number of items per page
            
        Returns:
            Tuple of (calls_list, total_count)
        """
        try:
            # Build base query with tenant isolation (exclude soft-deleted)
            query = self.db.query(CallLog).join(Lead).filter(
                Lead.tenant_id == self.tenant_id,
                CallLog.is_deleted == False
            )
            
            # Apply filters
            if sentiment:
                query = query.filter(CallLog.sentiment == sentiment)
            
            if outcome:
                query = query.filter(CallLog.outcome == outcome)
            
            if call_direction:
                query = query.filter(CallLog.call_direction == call_direction)
            
            if lead_id:
                query = query.filter(CallLog.lead_id == lead_id)
            
            if created_after:
                query = query.filter(CallLog.created_at >= created_after)
            
            if created_before:
                query = query.filter(CallLog.created_at <= created_before)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * limit
            calls = query.options(joinedload(CallLog.lead)).order_by(desc(CallLog.created_at)).offset(offset).limit(limit).all()
            
            # Format response
            calls_list = []
            for call in calls:
                call_data = {
                    "id": call.id,
                    "lead_id": call.lead_id,
                    "lead_name": call.lead.name if call.lead else "Unknown",
                    "call_direction": call.call_direction,
                    "duration": call.duration,
                    "transcript": call.transcript,
                    "summary": call.summary,
                    "sentiment": call.sentiment,
                    "outcome": call.outcome,
                    "recording_url": call.recording_url,
                    "cost": call.cost,
                    "created_at": call.created_at,
                    "updated_at": call.updated_at
                }
                calls_list.append(call_data)
            
            self.logger.info(f"Retrieved {len(calls_list)} calls (page {page}/{math.ceil(total_count/limit) if total_count > 0 else 1})")
            return calls_list, total_count
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve calls: {str(e)}")
            raise
    
    def get_call_by_id(self, call_id: UUID) -> Dict[str, Any]:
        """
        Get call by ID with tenant validation
        
        Args:
            call_id: Call ID to retrieve
            
        Returns:
            Call data with lead information
            
        Raises:
            CallNotFoundError: If call doesn't exist or belongs to different tenant
        """
        try:
            call = self.db.query(CallLog).join(Lead).filter(
                and_(
                    CallLog.id == call_id,
                    Lead.tenant_id == self.tenant_id
                )
            ).options(joinedload(CallLog.lead)).first()
            
            if not call:
                self.logger.error(f"Call {call_id} not found for tenant {self.tenant_id}")
                raise CallNotFoundError(f"Call {call_id} not found")
            
            call_data = {
                "id": call.id,
                "lead_id": call.lead_id,
                "lead": {
                    "id": call.lead.id,
                    "name": call.lead.name,
                    "phone": call.lead.phone,
                    "email": call.lead.email,
                    "source": call.lead.source
                } if call.lead else None,
                "call_direction": call.call_direction,
                "duration": call.duration,
                "transcript": call.transcript,
                "summary": call.summary,
                "sentiment": call.sentiment,
                "outcome": call.outcome,
                "recording_url": call.recording_url,
                "cost": call.cost,
                "created_at": call.created_at,
                "updated_at": call.updated_at
            }
            
            self.logger.info(f"Retrieved call {call_id}")
            return call_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve call {call_id}: {str(e)}")
            raise
    
    def update_call(
        self,
        call_id: UUID,
        transcript: Optional[str] = None,
        summary: Optional[str] = None,
        sentiment: Optional[str] = None,
        outcome: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Update call log with new information
        
        Args:
            call_id: Call ID to update
            transcript: Updated transcript
            summary: Updated summary
            sentiment: Updated sentiment
            outcome: Updated outcome
            notes: Additional notes
            user_id: ID of user making the update
            
        Returns:
            Updated call data
            
        Raises:
            CallNotFoundError: If call doesn't exist or belongs to different tenant
        """
        try:
            # Find call with tenant validation
            call = self.db.query(CallLog).join(Lead).filter(
                and_(
                    CallLog.id == call_id,
                    Lead.tenant_id == self.tenant_id
                )
            ).first()
            
            if not call:
                self.logger.error(f"Call {call_id} not found for tenant {self.tenant_id}")
                raise CallNotFoundError(f"Call {call_id} not found")
            
            # Track changes for analytics
            changes = {}
            
            if transcript is not None:
                call.transcript = transcript
                changes['transcript'] = 'updated'
                
                # Re-analyze sentiment if transcript changed
                if not sentiment:
                    new_sentiment = self.analyze_sentiment(transcript)
                    if new_sentiment != call.sentiment:
                        call.sentiment = new_sentiment
                        changes['sentiment'] = f'{call.sentiment} -> {new_sentiment}'
            
            if summary is not None:
                changes['summary'] = 'updated'
                call.summary = summary
            
            if sentiment is not None:
                old_sentiment = call.sentiment
                call.sentiment = sentiment
                changes['sentiment'] = f'{old_sentiment} -> {sentiment}'
            
            if outcome is not None:
                old_outcome = call.outcome
                call.outcome = outcome
                changes['outcome'] = f'{old_outcome} -> {outcome}'
            
            if notes is not None:
                changes['notes'] = 'updated'
                # Assuming there's a notes field or we store it somewhere
            
            call.updated_at = datetime.utcnow()
            
            # Log analytics event
            if changes:
                self._log_analytics_event(
                    event_type=EventType.CALL_UPDATED.value,
                    entity_type="call",
                    entity_id=call.id,
                    metadata={
                        "changes": changes,
                        "lead_id": str(call.lead_id)
                    },
                    user_id=user_id
                )
            
            self.db.commit()
            
            # Return updated call data
            updated_call = self.get_call_by_id(call_id)
            
            self.logger.info(f"✓ Updated call {call_id}")
            return updated_call
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update call {call_id}: {str(e)}")
            raise
    
    def _log_analytics_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ):
        """
        Log analytics event for call operations
        
        Args:
            event_type: Type of event
            entity_type: Type of entity
            entity_id: ID of entity
            metadata: Additional event metadata
            user_id: ID of user performing the action
        """
        try:
            event = AnalyticsEvent(
                tenant_id=self.tenant_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=metadata or {},
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(event)
            # Note: We don't commit here as it's usually part of a larger transaction
            
        except Exception as e:
            self.logger.warning(f"Failed to log analytics event {event_type}: {str(e)}")
            # Don't raise - analytics failure shouldn't break main operations

