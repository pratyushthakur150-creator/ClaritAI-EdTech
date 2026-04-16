from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db_session as get_db
from app.core.utils import ensure_uuid
from app.services.chatbot_service import ChatbotService
from app.models import Lead, LeadSource
import uuid
import logging
from fastapi import HTTPException, status

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)


@router.get("/config/{tenant_id}")
async def get_chatbot_config(tenant_id: str, db: Session = Depends(get_db)):
    """Return chatbot widget configuration for a tenant."""
    return {
        "tenant_id": tenant_id,
        "theme": {
            "primaryColor": "#4F46E5",
            "position": "bottom-right",
            "greeting": "Hi! How can I help you regarding admissions?"
        }
    }


@router.post("/message")
async def chatbot_message(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle incoming chatbot message using AI service."""
    try:
        body = await request.json()
        message = body.get("message", "")
        tenant_str = body.get("tenant_id", "")
        visitor_str = body.get("visitor_id")

        if not message:
            return {"status": "error", "response": "Message is required"}

        if not tenant_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID required"
            )

        try:
            tenant_id = ensure_uuid(tenant_str)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Tenant ID format: {str(e)}"
            )

        # Initialize service
        service = ChatbotService(db)

        # Manage visitor/session ID (accept any string so Aria widget "aria-xxx" keeps same session)
        if visitor_str and str(visitor_str).strip():
            session_id = str(visitor_str).strip()
            try:
                uuid.UUID(session_id)
            except (ValueError, TypeError):
                pass  # keep session_id as-is for non-UUID widgets (e.g. aria-xxx)
        else:
            session_id = str(uuid.uuid4())

        # ── DB session management ────────────────────────────────────
        db_session = None
        conversation_history = []
        try:
            db_session = service.get_session_by_visitor_id(session_id, tenant_id)
            if not db_session:
                db_session = service.create_session(
                    tenant_id=tenant_id,
                    visitor_id=session_id,
                    initial_message=message,
                )
            else:
                service.send_message(
                    session_id=db_session.id,
                    message=message,
                    sender="user",
                    tenant_id=tenant_id,
                )

            # Pull conversation history for AI context
            if db_session and db_session.conversation:
                conversation_history = db_session.conversation
        except Exception as e:
            # CRITICAL: rollback so the DB session is usable for lead capture
            db.rollback()
            # Handle tenant foreign key error gracefully
            if "not present in table \"tenants\"" in str(e):
                logger.warning(f"Tenant {tenant_id} not found in database - continuing without session save")
                db_session = None
            else:
                logger.warning(f"DB session management failed (non-critical): {e}")
                db_session = None

        # ── Build exam context for Aria (UPSC/NEET/JEE/CAT/GMAT) ─────
        exam_target = (body.get("exam_target") or "").strip() or None
        preparation_stage = (body.get("preparation_stage") or "").strip() or None
        extra_context = []
        if exam_target or preparation_stage:
            parts = []
            if exam_target:
                parts.append(f"User is targeting: {exam_target}.")
            if preparation_stage:
                parts.append(f"Preparation stage: {preparation_stage}.")
            extra_context.append({"name": "aria_exam_context", "content": " ".join(parts) + " Answer fee, syllabus, and strategy questions in this exam's context. Be concise (1-3 sentences)."})

        # ── Generate AI response (critical) ──────────────────────────
        ai_result = await service.generate_ai_response(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history,
            context=extra_context,
            tenant_id=tenant_id,
        )

        # ── Save bot response to DB (non-critical) ──────────────────
        if db_session:
            try:
                service.send_message(
                    session_id=db_session.id,
                    message=ai_result["response"],
                    sender="bot",
                    tenant_id=tenant_id,
                )
            except Exception as e:
                logger.warning(f"Failed to save bot response to DB: {e}")
                db.rollback()  # CRITICAL: clean up failed transaction for lead capture

        # ── Auto-capture lead if contact info found ──────────────────
        should_capture = ai_result.get("should_capture_lead", False)
        lead_captured = False
        
        logger.info(f"🔍 [LEAD-CAPTURE] tenant={tenant_id} message='{message[:80]}' db_session={'YES' if db_session else 'NONE'}")
        
        # ── Only capture leads when email OR phone is in the CURRENT message ──
        # The widget reuses the same visitor_id across conversations, so
        # conversation_history may contain old contact info. We only capture when
        # the user provides an email or phone in THIS specific message.
        import re as _re
        _email_in_current = _re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message
        )
        _phone_in_current = _re.search(
            r'(?:\+?91[\s\-]?)?[6-9]\d{9}', message
        ) or _re.search(
            r'\+?\d[\d\s\-()]{9,}', message
        )

        if _email_in_current or _phone_in_current:
            lead_data = service.extract_lead_info(message, conversation_history)

            # If the widget sent an explicit exam_target (UPSC/NEET/JEE/CAT/GMAT),
            # prefer that as the course label instead of any stale course keyword
            # detected from an old conversation using the same visitor_id.
            if exam_target:
                lead_data["course"] = exam_target

            logger.info(
                f"🔍 [LEAD-CAPTURE] Extracted: name={lead_data.get('name')} "
                f"email={lead_data.get('email')} phone={lead_data.get('phone')} "
                f"course={lead_data.get('course')}"
            )

            try:
                from app.models import Lead as LeadModel
                existing = None
                
                # Check for duplicate by email OR phone
                if lead_data.get('email'):
                    existing = db.query(LeadModel).filter(
                        LeadModel.email == lead_data['email'],
                        LeadModel.tenant_id == tenant_id
                    ).first()
                elif lead_data.get('phone'):
                    existing = db.query(LeadModel).filter(
                        LeadModel.phone == lead_data['phone'],
                        LeadModel.tenant_id == tenant_id
                    ).first()

                if existing:
                    logger.info(f"🔍 [LEAD-CAPTURE] Contact already exists as lead {existing.id} — skipping")
                    lead_captured = True
                    should_capture = False
                elif lead_data.get('email') or lead_data.get('phone'):
                    logger.info(f"🔍 [LEAD-CAPTURE] Creating NEW lead for email={lead_data.get('email')} phone={lead_data.get('phone')} tenant={tenant_id}")
                    lead_id = await service.capture_lead(lead_data, tenant_id, session_id)
                    logger.info(f"🔍 [LEAD-CAPTURE] capture_lead returned: {lead_id}")
                    if lead_id:
                        lead_captured = True
                        should_capture = False

                        if db_session:
                            try:
                                db_session.lead_id = lead_id
                                db_session.lead_captured = 'true'
                                db.commit()
                                logger.info(f"✅ Linked session {session_id} to lead {lead_id}")
                            except Exception as e:
                                logger.error(f"Failed to link session to lead: {e}", exc_info=True)
                                db.rollback()

                        response_message = f"Thank you, {lead_data['name']}! I've captured your details"
                        if lead_data.get('course'):
                            response_message += f" for {lead_data['course']}"
                        response_message += f". Our team will contact you at {lead_data['email']} soon."
                        ai_result["response"] = response_message
                    else:
                        logger.error(f"🔍 [LEAD-CAPTURE] capture_lead FAILED (returned None)")
            except Exception as e:
                logger.error(f"❌ [LEAD-CAPTURE] Exception: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.info(f"🔍 [LEAD-CAPTURE] No email in current message — skipping capture")

        response = {
            "response": ai_result["response"],
            "status": "success",
            "visitor_id": session_id,
            "intent": ai_result.get("intent"),
            "should_capture_lead": should_capture,
            "lead_captured": lead_captured,
        }
        
        # Include lead_id if captured (store it from earlier capture attempt)
        if lead_captured:
            try:
                # Get the lead_id from the session if available
                if db_session and db_session.lead_id:
                    response["lead_id"] = str(db_session.lead_id)
            except:
                pass  # Don't fail if we can't get lead_id
        
        return response

    except Exception as e:
        logger.error(f"Error processing chatbot message: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I'm sorry, something went wrong. Please try again.",
            "status": "error",
        }


@router.post("/capture-lead")
async def capture_lead_from_chatbot(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for Aria/widget lead capture. Creates a lead without JWT.
    Body: tenant_id, visitor_id (session_id), name, phone, email (optional),
    exam_target, preparation_stage, city. Maps to Lead model and ChatbotService.capture_lead.
    """
    try:
        body = await request.json()
        tenant_str = body.get("tenant_id", "")
        visitor_str = body.get("visitor_id") or body.get("session_id", "")
        name = (body.get("name") or "").strip()
        phone = (body.get("phone") or "").strip()
        email = (body.get("email") or "").strip() or None
        exam_target = (body.get("exam_target") or "").strip() or None
        preparation_stage = (body.get("preparation_stage") or "").strip() or None
        city = (body.get("city") or "").strip() or None

        if not tenant_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id required"
            )
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="name required"
            )
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="phone required"
            )

        try:
            tenant_id = ensure_uuid(tenant_str)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tenant_id: {str(e)}"
            )

        session_id = visitor_str if visitor_str else str(uuid.uuid4())

        lead_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "exam_target": exam_target,
            "preparation_stage": preparation_stage,
            "city": city,
            "source": "website_chatbot",
        }
        if exam_target:
            lead_data["course"] = exam_target

        service = ChatbotService(db)
        lead_id = await service.capture_lead(
            lead_data=lead_data,
            tenant_id=tenant_id,
            session_id=session_id,
        )

        if not lead_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lead"
            )

        return {
            "status": "success",
            "lead_id": str(lead_id),
            "message": "Lead captured successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in capture-lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture lead"
        )


@router.get("/stats")
async def get_chatbot_stats(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),
    db: Session = Depends(get_db),
):
    """Get chatbot statistics — pulls real data from DB."""
    try:
        tid = None
        # Use explicit query param first, then fall back to auth context
        if tenant_id:
            try:
                tid = uuid.UUID(tenant_id)
            except ValueError:
                pass
        elif hasattr(request.state, "current_tenant") and request.state.current_tenant:
            try:
                tid_str = getattr(request.state.current_tenant, "tenant_id", None)
                if tid_str:
                    tid = uuid.UUID(str(tid_str))
            except (ValueError, AttributeError, TypeError):
                pass

        service = ChatbotService(db)
        return service.get_stats(tenant_id=tid)
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_chatbot_sessions(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent chatbot sessions — pulls real data from DB."""
    try:
        tid = None
        if tenant_id:
            try:
                tid = uuid.UUID(tenant_id)
            except ValueError:
                pass
        elif hasattr(request.state, "current_tenant") and request.state.current_tenant:
            try:
                tid_str = getattr(request.state.current_tenant, "tenant_id", None)
                if tid_str:
                    tid = uuid.UUID(str(tid_str))
            except (ValueError, AttributeError, TypeError):
                pass

        service = ChatbotService(db)
        sessions = service.get_sessions(tenant_id=tid, limit=limit)
        return {"data": sessions, "total": len(sessions), "limit": limit}
    except Exception as e:
        logger.error(f"Error getting chatbot sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/reload-exam-knowledge")
async def reload_exam_knowledge():
    """Admin endpoint: Force reload all exam knowledge documents into ChromaDB."""
    try:
        from app.rag.chatbot_rag.exam_knowledge_loader import load_all_exams
        results = await load_all_exams(force_reload=True)
        loaded = [k for k, v in results.items() if v]
        failed = [k for k, v in results.items() if not v]
        return {
            "status": "success",
            "loaded": loaded,
            "failed": failed,
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error reloading exam knowledge: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload exam knowledge: {str(e)}"
        )

