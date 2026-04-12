"""
Enrollment service for AI EdTech CRM platform.
Handles enrollment creation, updates, and teaching assistant activation.
"""

from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID, uuid4
import json
import logging
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func, desc, or_

# CORRECTED IMPORTS for your backend structure
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse

# Import models
from app.models.enrollment import Enrollment, Student, PaymentStatus
from app.models.lead import Lead, LeadStatus
from app.models.teaching import Course

# Setup logging
logger = logging.getLogger(__name__)


class EnrollmentService:
    """Service class for handling enrollment operations."""

    def __init__(self, db: Session, redis_client, tenant_id: UUID):
        """
        Initialize enrollment service.
        
        Args:
            db: Database session
            redis_client: Redis client for tracking and caching
            tenant_id: Tenant ID for multi-tenant isolation
        """
        self.db = db
        self.redis_client = redis_client
        self.tenant_id = tenant_id

    def create_enrollment(self, enrollment_data: EnrollmentCreate) -> EnrollmentResponse:
        """
        Create new enrollment with complete workflow.
        
        Args:
            enrollment_data: Enrollment creation data
            
        Returns:
            EnrollmentResponse: Created enrollment with nested data
            
        Raises:
            ValueError: If lead not found, course not accessible, or creation fails
        """
        try:
            # 1. Fetch and validate lead with tenant access
            lead = self.db.query(Lead).filter(
                and_(
                    Lead.id == enrollment_data.lead_id,
                    Lead.tenant_id == self.tenant_id
                )
            ).first()
            
            if not lead:
                logger.error(f"Lead {enrollment_data.lead_id} not found for tenant {self.tenant_id}")
                raise ValueError("Lead not found or access denied")

            # Verify course exists and is accessible to tenant
            course = self.db.query(Course).filter(
                and_(
                    Course.id == enrollment_data.course_id,
                    Course.tenant_id == self.tenant_id
                )
            ).first()
            
            if not course:
                logger.error(f"Course {enrollment_data.course_id} not found for tenant {self.tenant_id}")
                raise ValueError("Course not found or access denied")

            # Check if lead is already enrolled in this course
            existing_enrollment = self.db.query(Enrollment).filter(
                and_(
                    Enrollment.lead_id == enrollment_data.lead_id,
                    Enrollment.course_id == enrollment_data.course_id,
                    Enrollment.tenant_id == self.tenant_id
                )
            ).first()
            
            if existing_enrollment:
                raise ValueError("Lead is already enrolled in this course")

            # 2. Create enrollment record
            enrollment = Enrollment(
                id=uuid4(),
                lead_id=enrollment_data.lead_id,
                course_id=enrollment_data.course_id,
                batch_id=enrollment_data.batch_id,
                total_amount=enrollment_data.total_amount,
                payment_status=enrollment_data.payment_status,
                amount_paid=enrollment_data.amount_paid,
                enrolled_at=datetime.utcnow(),
                tenant_id=self.tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(enrollment)
            self.db.flush()  # Get the ID without committing
            
            # 3. Update lead status to "enrolled"
            lead.status = LeadStatus.ENROLLED
            lead.updated_at = datetime.utcnow()
            
            # 4. Create student record (for teaching assistant module)
            student = Student(
                id=uuid4(),
                enrollment_id=enrollment.id,
                lead_id=enrollment_data.lead_id,
                lms_user_id=f"student_{uuid4().hex[:8]}",
                tenant_id=self.tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(student)
            # enrollment.student_id = student.id  # REMOVED: Enrollment has no student_id column
            
            # Commit all changes
            self.db.commit()
            
            # 5. Log usage: increment Redis counter for enrollments
            try:
                self.redis_client.hincrby(f"usage:{self.tenant_id}:daily", "enrollments", 1)
                self.redis_client.hincrby(f"usage:{self.tenant_id}:monthly", "enrollments", 1)
                self.redis_client.hincrby(f"usage:{self.tenant_id}:daily", "students", 1)
                self.redis_client.hincrby(f"usage:{self.tenant_id}:monthly", "students", 1)
            except Exception as redis_error:
                logger.warning(f"Redis usage tracking failed: {redis_error}")
            
            # 6. Send LMS credentials email (stub: just log it)
            logger.info(f"LMS Credentials Email - Student: {lead.name}, Course: {course.name}, "
                       f"Username: {student.lms_user_id}, Enrollment ID: {enrollment.id}")
            
            # 7. Return enrollment with nested lead/course data
            return self._build_enrollment_response(enrollment)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating enrollment: {str(e)}")
            raise ValueError("Failed to create enrollment")

    def get_enrollments(
        self,
        page: int = 1,
        per_page: int = 20,
        payment_status: Optional[str] = None,
        course_id: Optional[UUID] = None,
        enrolled_after: Optional[datetime] = None
    ) -> Tuple[List[EnrollmentResponse], int]:
        """
        Get enrollments with filtering and pagination.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            payment_status: Filter by payment status
            course_id: Filter by course ID
            enrolled_after: Filter enrollments after this date
            
        Returns:
            Tuple of (enrollments list, total count)
        """
        try:
            # Base query with tenant isolation
            query = self.db.query(Enrollment).filter(
                Enrollment.tenant_id == self.tenant_id
            ).options(
                selectinload(Enrollment.lead),
                selectinload(Enrollment.course)
            )
            
            # Apply filters
            if payment_status:
                query = query.filter(Enrollment.payment_status == payment_status)
            
            if course_id:
                query = query.filter(Enrollment.course_id == course_id)
            
            if enrolled_after:
                query = query.filter(Enrollment.enrolled_at >= enrolled_after)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            enrollments = query.order_by(desc(Enrollment.enrolled_at)).offset(offset).limit(per_page).all()
            
            # Build response objects
            enrollment_responses = [self._build_enrollment_response(e) for e in enrollments]
            
            return enrollment_responses, total_count
            
        except Exception as e:
            logger.error(f"Error fetching enrollments: {str(e)}")
            raise ValueError("Failed to retrieve enrollments")

    def get_enrollment_by_id(self, enrollment_id: UUID) -> EnrollmentResponse:
        """
        Get enrollment by ID with tenant access validation.
        
        Args:
            enrollment_id: Enrollment identifier
            
        Returns:
            EnrollmentResponse: Enrollment with nested data
            
        Raises:
            ValueError: If enrollment not found or access denied
        """
        try:
            enrollment = self.db.query(Enrollment).filter(
                and_(
                    Enrollment.id == enrollment_id,
                    Enrollment.tenant_id == self.tenant_id
                )
            ).options(
                selectinload(Enrollment.lead),
                selectinload(Enrollment.course),
                selectinload(Enrollment.student)
            ).first()
            
            if not enrollment:
                raise ValueError("Enrollment not found or access denied")
            
            return self._build_enrollment_response(enrollment)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching enrollment {enrollment_id}: {str(e)}")
            raise ValueError("Failed to retrieve enrollment")

    def update_enrollment(
        self,
        enrollment_id: UUID,
        update_data: EnrollmentUpdate
    ) -> EnrollmentResponse:
        """
        Update enrollment details.
        
        Args:
            enrollment_id: Enrollment identifier
            update_data: Fields to update
            
        Returns:
            EnrollmentResponse: Updated enrollment
            
        Raises:
            ValueError: If enrollment not found or update fails
        """
        try:
            # Fetch enrollment with tenant validation
            enrollment = self.db.query(Enrollment).filter(
                and_(
                    Enrollment.id == enrollment_id,
                    Enrollment.tenant_id == self.tenant_id
                )
            ).options(
                selectinload(Enrollment.lead),
                selectinload(Enrollment.course)
            ).first()
            
            if not enrollment:
                raise ValueError("Enrollment not found or access denied")
            
            # Track original values for analytics
            original_payment_status = enrollment.payment_status
            original_amount_paid = enrollment.amount_paid
            
            # Build update dictionary
            update_dict = update_data.model_dump(exclude_none=True)
            
            # Update fields
            for field, value in update_dict.items():
                setattr(enrollment, field, value)
            
            # Auto-calculate payment status if amount_paid changed but status not provided
            if 'amount_paid' in update_dict and 'payment_status' not in update_dict:
                if enrollment.amount_paid == 0:
                    enrollment.payment_status = PaymentStatus.PENDING
                elif enrollment.amount_paid >= enrollment.total_amount:
                    enrollment.payment_status = PaymentStatus.PAID
                else:
                    enrollment.payment_status = PaymentStatus.PARTIAL
            
            # Validate payment consistency
            if enrollment.amount_paid > enrollment.total_amount:
                raise ValueError("Amount paid cannot exceed total amount")
            
            enrollment.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log analytics event if payment changed
            if enrollment.payment_status != original_payment_status or enrollment.amount_paid != original_amount_paid:
                logger.info(
                    f"Payment updated for enrollment {enrollment_id}: "
                    f"status {original_payment_status} -> {enrollment.payment_status}, "
                    f"amount {original_amount_paid} -> {enrollment.amount_paid}"
                )
            
            return self._build_enrollment_response(enrollment)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating enrollment {enrollment_id}: {str(e)}")
            raise ValueError("Failed to update enrollment")

    def activate_teaching_assistant(self, enrollment_id: UUID) -> Dict[str, Any]:
        """
        Activate teaching assistant for enrolled student.
        
        Args:
            enrollment_id: Enrollment identifier
            
        Returns:
            Dict containing student_id, lms_user_id, course_id, assistant_access_token
            
        Raises:
            ValueError: If enrollment not found or activation fails
        """
        try:
            # 1. Fetch enrollment with student record
            enrollment = self.db.query(Enrollment).filter(
                and_(
                    Enrollment.id == enrollment_id,
                    Enrollment.tenant_id == self.tenant_id
                )
            ).options(
                selectinload(Enrollment.student),
                selectinload(Enrollment.lead),
                selectinload(Enrollment.course)
            ).first()
            
            if not enrollment:
                raise ValueError("Enrollment not found or access denied")
            
            # 2. Ensure student record exists
            student = enrollment.student
            if not student:
                # Create student record if missing
                student = Student(
                    id=uuid4(),
                    enrollment_id=enrollment.id,
                    lead_id=enrollment.lead_id,
                    course_id=enrollment.course_id,
                    name=enrollment.lead.name,
                    email=enrollment.lead.email,
                    phone=enrollment.lead.phone,
                    assistant_enabled=True,
                    lms_user_id=f"student_{uuid4().hex[:8]}",
                    tenant_id=self.tenant_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(student)
                enrollment.student_id = student.id
            else:
                # 3. Set assistant_enabled = True
                student.assistant_enabled = True
                student.updated_at = datetime.utcnow()
            
            # 4. Generate access token for teaching assistant (stub for MVP)
            assistant_access_token = f"ta_token_{uuid4().hex[:16]}"
            
            self.db.commit()
            
            logger.info(f"Teaching assistant activated for enrollment {enrollment_id}, student {student.id}")
            
            # 5. Return required data
            return {
                "student_id": str(student.id),
                "lms_user_id": student.lms_user_id,
                "course_id": str(enrollment.course_id),
                "assistant_access_token": assistant_access_token,
                "activation_status": "success",
                "activated_at": datetime.utcnow().isoformat()
            }
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error activating teaching assistant for enrollment {enrollment_id}: {str(e)}")
            raise ValueError("Failed to activate teaching assistant")

    def _build_enrollment_response(self, enrollment: Enrollment) -> EnrollmentResponse:
        """
        Build EnrollmentResponse from enrollment model.
        
        Args:
            enrollment: Enrollment model instance
            
        Returns:
            EnrollmentResponse: Formatted response object
        """
        # Build lead dictionary
        lead_dict = {
            "id": str(enrollment.lead.id),
            "name": enrollment.lead.name,
            "phone": enrollment.lead.phone
        }
        
        # Build course dictionary
        course_dict = {
            "id": str(enrollment.course.id),
            "name": enrollment.course.name
        }
        
        return EnrollmentResponse(
            id=enrollment.id,
            lead=lead_dict,
            course=course_dict,
            batch_id=enrollment.batch_id,
            enrolled_at=enrollment.enrolled_at,
            payment_status=enrollment.payment_status,
            total_amount=enrollment.total_amount,
            amount_paid=enrollment.amount_paid,
            student_id=enrollment.student.id if enrollment.student else None,
            created_at=enrollment.created_at
        )

    def get_enrollment_statistics(self) -> Dict[str, Any]:
        """
        Get enrollment statistics for tenant dashboard.
        
        Returns:
            Dict containing enrollment statistics
        """
        try:
            base_query = self.db.query(Enrollment).filter(Enrollment.tenant_id == self.tenant_id)
            
            # Total enrollments
            total_enrollments = base_query.count()
            
            # Payment status breakdown
            payment_stats = self.db.query(
                Enrollment.payment_status,
                func.count(Enrollment.id).label('count')
            ).filter(
                Enrollment.tenant_id == self.tenant_id
            ).group_by(Enrollment.payment_status).all()
            
            payment_breakdown = {status: count for status, count in payment_stats}
            
            # Revenue statistics
            revenue_stats = self.db.query(
                func.sum(Enrollment.total_amount).label('total_revenue'),
                func.sum(Enrollment.amount_paid).label('collected_revenue')
            ).filter(Enrollment.tenant_id == self.tenant_id).first()
            
            return {
                "total_enrollments": total_enrollments,
                "payment_breakdown": payment_breakdown,
                "total_revenue": float(revenue_stats.total_revenue or 0),
                "collected_revenue": float(revenue_stats.collected_revenue or 0),
                "outstanding_revenue": float((revenue_stats.total_revenue or 0) - (revenue_stats.collected_revenue or 0))
            }
            
        except Exception as e:
            logger.error(f"Error fetching enrollment statistics: {str(e)}")
            raise ValueError("Failed to fetch enrollment statistics")