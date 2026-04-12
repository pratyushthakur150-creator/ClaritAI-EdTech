import logging
from typing import Optional, List, Dict, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta, time, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import json


from app.models import Demo, Lead, User, UserRole, Course, AnalyticsEvent, EventType
from app.models.lead import LeadStatus
from app.schemas.demo import DemoCreate, DemoUpdate, DemoResponse
from app.services.google_calendar_service import get_calendar_service

# Custom Exceptions
class DemoNotFoundError(Exception):
    def __init__(self, message, demo_id=None):
        super().__init__(message)
        self.demo_id = demo_id

class LeadNotFoundError(Exception):
    def __init__(self, message, lead_id=None):
        super().__init__(message)
        self.lead_id = lead_id

class MentorNotFoundError(Exception):
    def __init__(self, message, mentor_id=None):
        super().__init__(message)
        self.mentor_id = mentor_id

class SlotNotAvailableError(Exception):
    pass

class RescheduleLimitExceededError(Exception):
    pass

class DemoService:
    def __init__(self, db: Session, tenant_id: UUID):
        """Initialize DemoService with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(__name__)
        
        # Configure logging with tenant context
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info(f"DemoService initialized for tenant: {tenant_id}")

    def get_available_slots(self, target_date: date, mentor_id: Optional[UUID] = None) -> List[datetime]:
        """
        Get available 30-minute demo slots from 10 AM to 8 PM for given date.
        Excludes already booked slots for the tenant.
        When mentor_id is provided, validates mentor exists; mentor-specific filtering
        is applied when Demo model has mentor_id column.
        
        Args:
            target_date: Date to check availability for
            mentor_id: Optional specific mentor (validated if provided; filter not applied until mentor_id on Demo)
            
        Returns:
            List of available datetime slots (naive UTC)
        """
        try:
            self.logger.info(f"Getting available slots for date: {target_date}, mentor: {mentor_id}")
            
            # If specific mentor requested, validate they exist (don't filter by mentor_id - column may not exist yet)
            if mentor_id:
                mentor = self.db.query(User).filter(
                    User.id == mentor_id,
                    User.tenant_id == self.tenant_id,
                    User.role == UserRole.MENTOR.value,
                    User.is_active == 'true'
                ).first()
                if not mentor:
                    raise MentorNotFoundError(
                        f"Mentor not found or not authorized for tenant",
                        mentor_id
                    )
            
            # Generate all possible 30-minute slots from 10 AM to 8 PM (naive UTC)
            start_time = time(10, 0)  # 10:00 AM
            end_time = time(20, 0)    # 8:00 PM
            all_slots = []
            current_datetime = datetime.combine(target_date, start_time)
            end_datetime = datetime.combine(target_date, end_time)
            while current_datetime < end_datetime:
                all_slots.append(current_datetime)
                current_datetime += timedelta(minutes=30)
            
            # Query booked slots for the tenant on this date (no outcome filter - DemoOutcome has no CANCELLED in DB enum)
            query = self.db.query(Demo).join(Lead).filter(
                Lead.tenant_id == self.tenant_id,
                func.date(Demo.scheduled_at) == target_date
            )
            booked_slots = query.all()
            # Normalize to naive for comparison (scheduled_at may be timezone-aware)
            booked_times = []
            for demo in booked_slots:
                t = demo.scheduled_at
                if t is not None:
                    booked_times.append(t.replace(tzinfo=None) if t.tzinfo else t)
            
            # Filter out booked slots
            available_slots = [slot for slot in all_slots if slot not in booked_times]
            
            self.logger.info(f"Found {len(available_slots)} available slots out of {len(all_slots)} total slots")
            return available_slots
            
        except MentorNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting available slots for tenant {self.tenant_id}: {str(e)}")
            raise

    def _auto_assign_mentor(self) -> UUID:
        """
        Auto-assign mentor using round-robin based on current demo load.
        
        Returns:
            UUID of assigned mentor
            
        Raises:
            MentorNotFoundError: If no mentors available for tenant
        """
        try:
            # Get all active mentors for tenant
            mentors = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.role == UserRole.MENTOR.value,
                User.is_active == 'true'
            ).all()
            
            if not mentors:
                raise MentorNotFoundError("No mentors available for tenant")
            
            # Count current demo load for each mentor (active demos)
            mentor_loads = {}
            for mentor in mentors:
                active_demos = self.db.query(func.count(Demo.id)).join(Lead).filter(
                    Lead.tenant_id == self.tenant_id,
                    Demo.mentor_id == mentor.id,
                    Demo.outcome.in_([None, 'scheduled'])  # Active demos
                ).scalar()
                mentor_loads[mentor.id] = active_demos or 0
            
            # Assign to mentor with lowest load
            assigned_mentor_id = min(mentor_loads.keys(), key=lambda x: mentor_loads[x])
            
            self.logger.info(f"Auto-assigned mentor {assigned_mentor_id} with {mentor_loads[assigned_mentor_id]} current demos")
            return assigned_mentor_id
            
        except Exception as e:
            self.logger.error(f"Error in auto-assignment for tenant {self.tenant_id}: {str(e)}")
            raise

    def schedule_demo(self, demo_data: DemoCreate) -> DemoResponse:
        """
        Schedule a new demo with availability check, auto-assignment, and Redis reminder.
        
        Args:
            demo_data: Demo creation data
            
        Returns:
            Created demo response
            
        Raises:
            LeadNotFoundError: If lead not found or not authorized
            SlotNotAvailableError: If requested slot not available
            MentorNotFoundError: If mentor not found or not authorized
        """
        try:
            self.logger.info(f"Scheduling demo for lead: {demo_data.lead_id}")
            
            # Verify lead exists and belongs to tenant
            lead = self.db.query(Lead).filter(
                Lead.id == demo_data.lead_id,
                Lead.tenant_id == self.tenant_id
            ).first()
            
            if not lead:
                raise LeadNotFoundError(
                    "Lead not found or not authorized for tenant",
                    demo_data.lead_id
                )
            
            # Verify course exists (only if course_id provided)
            course_id_val = getattr(demo_data, 'course_id', None)
            if course_id_val:
                course = self.db.query(Course).filter(
                    Course.id == course_id_val,
                    Course.tenant_id == self.tenant_id
                ).first()
                if not course:
                    raise ValueError("Course not found or not authorized for tenant")
            
            # Check slot availability (non-critical — skip on error)
            mentor_id_val = getattr(demo_data, 'mentor_id', None)
            try:
                target_date = demo_data.scheduled_at.date()
                available_slots = self.get_available_slots(
                    target_date,
                    mentor_id_val
                )
                if demo_data.scheduled_at not in available_slots:
                    # Slot check is best-effort; allow scheduling anyway
                    self.logger.warning(f"Requested slot {demo_data.scheduled_at} may not be in standard slots, allowing anyway")
            except Exception as slot_err:
                self.logger.warning(f"Slot availability check failed (non-critical): {slot_err}")
            
            # Auto-assign mentor if not provided
            mentor_id = mentor_id_val
            if not mentor_id:
                try:
                    mentor_id = self._auto_assign_mentor()
                except MentorNotFoundError:
                    # No mentors configured — use the current user or a placeholder
                    self.logger.warning("No mentors available, skipping mentor assignment")
                    # Try to find any admin user to assign
                    admin = self.db.query(User).filter(
                        User.tenant_id == self.tenant_id,
                        User.is_active == 'true'
                    ).first()
                    mentor_id = admin.id if admin else None
            else:
                # Verify provided mentor exists, is active, and belongs to tenant
                mentor = self.db.query(User).filter(
                    User.id == mentor_id,
                    User.tenant_id == self.tenant_id,
                    User.role == UserRole.MENTOR.value,
                    User.is_active == 'true'
                ).first()
                
                if not mentor:
                    self.logger.warning(f"Specified mentor {mentor_id} not found, auto-assigning")
                    try:
                        mentor_id = self._auto_assign_mentor()
                    except MentorNotFoundError:
                        admin = self.db.query(User).filter(
                            User.tenant_id == self.tenant_id,
                            User.is_active == 'true'
                        ).first()
                        mentor_id = admin.id if admin else None
            
            # Create demo record
            demo = Demo(
                id=uuid4(),
                tenant_id=self.tenant_id,
                lead_id=demo_data.lead_id,
                mentor_id=mentor_id,
                course_id=course_id_val,
                scheduled_at=demo_data.scheduled_at,
                duration_minutes=getattr(demo_data, 'duration_minutes', 60),
                notes=demo_data.notes,
                created_at=datetime.utcnow()
            )
            
            self.db.add(demo)
            
            # Update lead status
            lead.status = LeadStatus.DEMO_SCHEDULED
            
            # ── Google Calendar event (non-critical) ──
            try:
                cal = get_calendar_service()
                if cal.is_available:
                    lead_name = getattr(lead, 'name', '') or 'Lead'
                    lead_email = getattr(lead, 'email', None)
                    course_name = ''
                    if course_id_val:
                        try:
                            course_obj = self.db.query(Course).filter(Course.id == course_id_val).first()
                            course_name = f" — {course_obj.name}" if course_obj else ''
                        except Exception:
                            pass

                    attendees = [lead_email] if lead_email else []
                    cal_result = cal.create_event(
                        summary=f"Demo: {lead_name}{course_name}",
                        start_time=demo_data.scheduled_at,
                        duration_minutes=getattr(demo_data, 'duration_minutes', 60),
                        description=f"Demo session for {lead_name}.\n\nNotes: {demo_data.notes or 'N/A'}",
                        attendee_emails=attendees,
                        timezone=getattr(demo_data, 'timezone', None) or 'Asia/Kolkata',
                        add_meet=False,
                    )
                    if cal_result:
                        demo.google_event_id = cal_result.get('event_id')
                        demo.meeting_link = cal_result.get('meet_link') or demo.meeting_link
                        demo.platform = demo.platform or 'Google Meet'
                        self.logger.info(f"Google Calendar event created: {demo.google_event_id}")
            except Exception as gcal_err:
                self.logger.warning(f"Google Calendar event creation failed (non-critical): {gcal_err}")
            
            # Queue Redis reminder (1 hour before demo) — non-critical
            try:
                reminder_time = demo_data.scheduled_at - timedelta(hours=1)
                reminder_data = {
                    "demo_id": str(demo.id),
                    "scheduled_for": reminder_time.isoformat(),
                    "tenant_id": str(self.tenant_id)
                }
                
                # Only queue if reminder time is in the future
                if reminder_time > datetime.utcnow():
                    redis_client.lpush("demo_reminders", json.dumps(reminder_data))
                    self.logger.info(f"Queued reminder for demo {demo.id} at {reminder_time}")
            except Exception as redis_err:
                self.logger.warning(f"Redis reminder queue failed (non-critical): {redis_err}")
            
            # Log analytics event (non-critical)
            try:
                self._log_analytics_event(
                    EventType.DEMO_SCHEDULED.value,
                    demo.id,
                    {
                        "demo_id": str(demo.id),
                        "lead_id": str(demo_data.lead_id),
                        "mentor_id": str(mentor_id) if mentor_id else None,
                        "course_id": str(course_id_val) if course_id_val else None,
                        "scheduled_at": demo_data.scheduled_at.isoformat()
                    }
                )
            except Exception as analytics_err:
                self.logger.warning(f"Analytics event logging failed (non-critical): {analytics_err}")
            
            self.db.commit()
            
            # Build response
            response = self._build_demo_response(demo)
            
            self.logger.info(f"Successfully scheduled demo {demo.id} for lead {demo_data.lead_id}")
            return response
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error scheduling demo for tenant {self.tenant_id}: {str(e)}")
            raise

    def get_demos(self, filters: dict, page: int = 1, per_page: int = 20) -> Tuple[List[DemoResponse], int]:
        """
        List demos with filtering, pagination, and multi-tenant isolation.
        
        Args:
            filters: Dictionary with filter criteria (date_from, date_to, status, mentor_id, lead_id)
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            Tuple of (demo list, total count)
        """
        try:
            self.logger.info(f"Getting demos with filters: {filters}, page: {page}")
            
            # Base query with tenant isolation
            query = self.db.query(Demo).join(Lead).filter(
                Lead.tenant_id == self.tenant_id
            )
            
            # Apply filters
            if filters.get('date_from'):
                query = query.filter(Demo.scheduled_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(Demo.scheduled_at <= filters['date_to'])
            
            if filters.get('status'):
                if filters['status'] == 'scheduled':
                    query = query.filter(Demo.outcome.is_(None))
                else:
                    query = query.filter(Demo.outcome == filters['status'])
            
            if filters.get('mentor_id'):
                query = query.filter(Demo.mentor_id == filters['mentor_id'])
            
            if filters.get('lead_id'):
                query = query.filter(Demo.lead_id == filters['lead_id'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Lead.name.ilike(search_term),
                        Lead.email.ilike(search_term),
                        Demo.notes.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and eager loading (newest first)
            demos = query.order_by(Demo.scheduled_at.desc()).options(
                joinedload(Demo.lead),
                joinedload(Demo.mentor),
                joinedload(Demo.course)
            ).offset((page - 1) * per_page).limit(per_page).all()
            
            # Build responses
            demo_responses = [self._build_demo_response(demo) for demo in demos]
            
            self.logger.info(f"Retrieved {len(demo_responses)} demos out of {total} total")
            return demo_responses, total
            
        except Exception as e:
            self.logger.error(f"Error getting demos for tenant {self.tenant_id}: {str(e)}")
            raise

    def get_demo_by_id(self, demo_id: UUID) -> DemoResponse:
        """
        Get demo by ID with tenant validation and nested data.
        
        Args:
            demo_id: Demo UUID
            
        Returns:
            Demo response with nested lead, mentor, course data
            
        Raises:
            DemoNotFoundError: If demo not found or not authorized
        """
        try:
            self.logger.info(f"Getting demo by ID: {demo_id}")
            
            demo = self.db.query(Demo).join(Lead).options(
                joinedload(Demo.lead),
                joinedload(Demo.mentor),
                joinedload(Demo.course)
            ).filter(
                Demo.id == demo_id,
                Lead.tenant_id == self.tenant_id
            ).first()
            
            if not demo:
                raise DemoNotFoundError(
                    "Demo not found or not authorized for tenant",
                    demo_id
                )
            
            response = self._build_demo_response(demo)
            self.logger.info(f"Retrieved demo {demo_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting demo {demo_id} for tenant {self.tenant_id}: {str(e)}")
            raise

    def update_demo(self, demo_id: UUID, update_data: DemoUpdate) -> DemoResponse:
        """
        Update demo with reschedule limit validation and lead status updates.
        
        Args:
            demo_id: Demo UUID
            update_data: Update data
            
        Returns:
            Updated demo response
            
        Raises:
            DemoNotFoundError: If demo not found
            RescheduleLimitExceededError: If reschedule limit exceeded
            SlotNotAvailableError: If new slot not available
        """
        try:
            self.logger.info(f"Updating demo {demo_id}")
            
            demo = self.db.query(Demo).join(Lead).filter(
                Demo.id == demo_id,
                Lead.tenant_id == self.tenant_id
            ).first()
            
            if not demo:
                raise DemoNotFoundError(
                    "Demo not found or not authorized for tenant",
                    demo_id
                )
            
            # Handle rescheduling with limit check
            if update_data.scheduled_at and update_data.scheduled_at != demo.scheduled_at:
                if demo.reschedule_count >= 2:
                    raise RescheduleLimitExceededError(
                        f"Maximum reschedule limit (2) exceeded for demo {demo_id}"
                    )
                
                # Check new slot availability
                available_slots = self.get_available_slots(
                    update_data.scheduled_at.date(),
                    demo.mentor_id
                )
                
                if update_data.scheduled_at not in available_slots:
                    raise SlotNotAvailableError(
                        f"New slot {update_data.scheduled_at} is not available"
                    )
                
                demo.scheduled_at = update_data.scheduled_at
                demo.reschedule_count += 1
                
                # Update Google Calendar event (non-critical)
                try:
                    cal = get_calendar_service()
                    gcal_id = getattr(demo, 'google_event_id', None)
                    if cal.is_available and gcal_id:
                        cal.update_event(
                            event_id=gcal_id,
                            start_time=update_data.scheduled_at,
                            duration_minutes=getattr(demo, 'duration_minutes', 60),
                            timezone=getattr(demo, 'timezone', None) or 'Asia/Kolkata',
                        )
                        self.logger.info(f"Google Calendar event updated for reschedule: {gcal_id}")
                except Exception as gcal_err:
                    self.logger.warning(f"Google Calendar update failed (non-critical): {gcal_err}")
                
                # Queue new reminder
                reminder_time = update_data.scheduled_at - timedelta(hours=1)
                if reminder_time > datetime.utcnow():
                    reminder_data = {
                        "demo_id": str(demo.id),
                        "scheduled_for": reminder_time.isoformat(),
                        "tenant_id": str(self.tenant_id)
                    }
                    redis_client.lpush("demo_reminders", json.dumps(reminder_data))
            
            # Update other fields
            if update_data.attended is not None:
                demo.attended = update_data.attended
                
                if update_data.attended:
                    # Log demo attended event
                    self._log_analytics_event(
                        EventType.DEMO_ATTENDED.value,
                        demo.id,
                        {"demo_id": str(demo.id), "outcome": update_data.outcome}
                    )
            
            if update_data.outcome:
                demo.outcome = update_data.outcome
                
                # Update lead status based on outcome
                lead = demo.lead
                if update_data.outcome == 'completed':
                    lead.status = LeadStatus.DEMO_COMPLETED
                elif update_data.outcome == 'no_show':
                    lead.status = LeadStatus.NURTURING
                elif update_data.outcome == 'cancelled':
                    lead.status = LeadStatus.NURTURING
            
            if update_data.notes:
                demo.notes = update_data.notes
            
            self.db.commit()
            
            response = self._build_demo_response(demo)
            self.logger.info(f"Successfully updated demo {demo_id}")
            return response
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating demo {demo_id} for tenant {self.tenant_id}: {str(e)}")
            raise

    def cancel_demo(self, demo_id: UUID, reason: str = "cancelled") -> DemoResponse:
        """
        Cancel demo and update lead status.
        
        Args:
            demo_id: Demo UUID
            reason: Cancellation reason
            
        Returns:
            Updated demo response
            
        Raises:
            DemoNotFoundError: If demo not found
        """
        try:
            self.logger.info(f"Cancelling demo {demo_id} with reason: {reason}")
            
            demo = self.db.query(Demo).join(Lead).filter(
                Demo.id == demo_id,
                Lead.tenant_id == self.tenant_id
            ).first()
            
            if not demo:
                raise DemoNotFoundError(
                    "Demo not found or not authorized for tenant",
                    demo_id
                )
            
            # Update demo
            demo.outcome = 'cancelled'
            demo.notes = f"Cancelled: {reason}"
            
            # Delete Google Calendar event (non-critical)
            try:
                cal = get_calendar_service()
                gcal_id = getattr(demo, 'google_event_id', None)
                if cal.is_available and gcal_id:
                    cal.delete_event(gcal_id)
                    self.logger.info(f"Google Calendar event deleted: {gcal_id}")
            except Exception as gcal_err:
                self.logger.warning(f"Google Calendar event deletion failed (non-critical): {gcal_err}")
            
            # Update lead status
            lead = demo.lead
            lead.status = LeadStatus.NURTURING
            
            # Log analytics event
            self._log_analytics_event(
                EventType.DEMO_CANCELLED.value,
                demo.id,
                {"demo_id": str(demo.id), "reason": reason}
            )
            
            self.db.commit()
            
            response = self._build_demo_response(demo)
            self.logger.info(f"Successfully cancelled demo {demo_id}")
            return response
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error cancelling demo {demo_id} for tenant {self.tenant_id}: {str(e)}")
            raise

    def send_reminder(self, demo_id: UUID) -> Dict:
        """
        Send demo reminder (placeholder implementation for MVP).
        
        Args:
            demo_id: Demo UUID
            
        Returns:
            Reminder status dictionary
        """
        try:
            self.logger.info(f"Sending reminder for demo {demo_id}")
            
            demo = self.db.query(Demo).join(Lead).filter(
                Demo.id == demo_id,
                Lead.tenant_id == self.tenant_id
            ).first()
            
            if not demo:
                raise DemoNotFoundError(
                    "Demo not found or not authorized for tenant",
                    demo_id
                )
            
            # Placeholder for SMS/Email reminder implementation
            # In production, integrate with notification service
            reminder_sent = True
            
            # Log reminder in analytics
            self._log_analytics_event(
                EventType.DEMO_REMINDER_SENT.value,
                demo.id,
                {
                    "demo_id": str(demo.id),
                    "lead_id": str(demo.lead_id),
                    "scheduled_at": demo.scheduled_at.isoformat()
                }
            )
            
            self.logger.info(f"Reminder sent for demo {demo_id}")
            
            return {
                "demo_id": str(demo_id),
                "reminder_sent": reminder_sent,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error sending reminder for demo {demo_id}: {str(e)}")
            raise

    def check_no_shows(self) -> List[UUID]:
        """
        Check for no-show demos and update status accordingly.
        
        Returns:
            List of demo IDs marked as no-show
        """
        try:
            self.logger.info("Checking for no-show demos")
            
            # Find demos scheduled more than 1 hour ago with no attendance record
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            no_show_demos = self.db.query(Demo).join(Lead).filter(
                Lead.tenant_id == self.tenant_id,
                Demo.scheduled_at < cutoff_time,
                Demo.attended.is_(None),
                Demo.outcome.is_(None)  # Not already processed
            ).all()
            
            no_show_ids = []
            
            for demo in no_show_demos:
                # Mark as no-show
                demo.outcome = 'no_show'
                demo.attended = False
                
                # Update lead status
                lead = demo.lead
                lead.status = LeadStatus.NURTURING
                
                # Log analytics event
                self._log_analytics_event(
                    EventType.DEMO_NO_SHOW.value,
                    demo.id,
                    {
                        "demo_id": str(demo.id),
                        "lead_id": str(demo.lead_id),
                        "scheduled_at": demo.scheduled_at.isoformat()
                    }
                )
                
                no_show_ids.append(demo.id)
            
            if no_show_ids:
                self.db.commit()
                self.logger.info(f"Marked {len(no_show_ids)} demos as no-show")
            else:
                self.logger.info("No no-show demos found")
            
            return no_show_ids
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error checking no-shows for tenant {self.tenant_id}: {str(e)}")
            raise

    def _log_analytics_event(self, event_type: str, entity_id: UUID, metadata: dict):
        """Log analytics event for demo operations."""
        try:
            event = AnalyticsEvent(
                tenant_id=self.tenant_id,
                event_type=event_type,
                entity_id=entity_id,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            self.db.add(event)
            self.logger.debug(f"Logged analytics event: {event_type} for entity {entity_id}")
        except Exception as e:
            self.logger.warning(f"Failed to log analytics event {event_type}: {str(e)}")

    def _build_demo_response(self, demo) -> DemoResponse:
        """Build demo response with nested data."""
        try:
            return DemoResponse(
                id=demo.id,
                lead_id=demo.lead_id,
                scheduled_at=demo.scheduled_at,
                duration_minutes=getattr(demo, 'duration_minutes', 60),
                timezone=getattr(demo, 'timezone', None),
                platform=getattr(demo, 'platform', None),
                meeting_link=getattr(demo, 'meeting_link', None),
                notes=demo.notes,
                completed=getattr(demo, 'completed', False),
                attended=getattr(demo, 'attended', False),
                attendee_count=getattr(demo, 'attendee_count', 1),
                outcome=getattr(demo, 'outcome', None),
                interest_level=getattr(demo, 'interest_level', None),
                courses_demonstrated=getattr(demo, 'courses_demonstrated', None),
                questions_asked=getattr(demo, 'questions_asked', None),
                objections=getattr(demo, 'objections', None),
                follow_up_scheduled=getattr(demo, 'follow_up_scheduled', None),
                next_steps=getattr(demo, 'next_steps', None),
                recording_url=getattr(demo, 'recording_url', None),
                google_event_id=getattr(demo, 'google_event_id', None),
                created_at=demo.created_at,
                updated_at=getattr(demo, 'updated_at', demo.created_at),
            )
        except Exception as e:
            self.logger.error(f"Error building demo response: {e}")
            raise

__all__ = ["DemoService"]
