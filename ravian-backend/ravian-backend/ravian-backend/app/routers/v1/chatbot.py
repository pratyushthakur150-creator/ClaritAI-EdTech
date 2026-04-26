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
    """Handle incoming chatbot message using AI service (Sia v2.0 for SSSi)."""
    try:
        body = await request.json()
        message = body.get("message", "")
        tenant_str = body.get("tenant_id", "")
        visitor_str = body.get("visitor_id")

        if not message:
            return {"status": "error", "response": "Message is required"}

        # ── Sia v2.0: Accept session_state from widget ─────────────
        session_state = body.get("session_state") or {}

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

        # ── Sia v2.0: Merge widget session_state with exam fields ────
        if exam_target and not session_state.get("goal"):
            session_state["goal"] = exam_target
        if preparation_stage and not session_state.get("preparation_stage"):
            session_state["preparation_stage"] = preparation_stage

        # ── Generate AI response (critical) ──────────────────────────
        ai_result = await service.generate_ai_response(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history,
            context=extra_context,
            tenant_id=tenant_id,
            session_state=session_state,
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

        # ── Email enforcement: if phone was just given but AI skipped email step ──
        import re as _re_email
        _phone_just_given = bool(_re_email.search(r'(?:\+?91[\s\-]?)?[6-9]\d{9}', message))
        _email_already_known = bool(session_state.get("email"))
        _response_asks_email = bool(_re_email.search(r'email|e-mail|mail id|email id|📧', ai_result["response"], _re_email.IGNORECASE))
        
        if _phone_just_given and not _email_already_known and not _response_asks_email:
            # The AI skipped the email step — append it to the response
            user_name = session_state.get("name") or "there"
            email_prompt = f"\n\nAlso, {user_name} — could you share your email ID? We'll send your class schedule and study material there. 📧 [Skip for now]"
            ai_result["response"] += email_prompt
            logger.info(f"📧 [EMAIL-ENFORCE] Injected email prompt (AI skipped it)")

        # ── Auto-capture lead if contact info found ──────────────────
        should_capture = ai_result.get("should_capture_lead", False)
        lead_captured = False
        
        logger.info(f"🔍 [LEAD-CAPTURE] tenant={tenant_id} message='{message[:80]}' db_session={'YES' if db_session else 'NONE'}")
        logger.info(f"🔍 [LEAD-CAPTURE] session_state: name={session_state.get('name')!r} phone={session_state.get('phone')!r} email={session_state.get('email')!r}")
        
        # ── Capture leads when contact info is in message OR session_state ──
        import re as _re
        _email_in_current = _re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message
        )
        _phone_in_current = _re.search(
            r'(?:\+?91[\s\-]?)?[6-9]\d{9}', message
        ) or _re.search(
            r'\+?\d[\d\s\-()]{9,}', message
        )

        # Also check session_state from Sia widget (it tracks name/phone there)
        _name_in_state = session_state.get("name")
        _phone_in_state = session_state.get("phone")
        _has_contact_in_state = bool(_name_in_state and _phone_in_state)

        if _email_in_current or _phone_in_current or _has_contact_in_state:
            lead_data = service.extract_lead_info(message, conversation_history)

            # ── Sia v2.0: Merge session_state into lead_data ─────────
            # The widget tracks name/grade/board/subjects in session_state,
            # which is MORE ACCURATE than what extract_lead_info infers from
            # bot text (which can hallucinate subjects like "AI & ML").
            if session_state.get("name") and (not lead_data.get("name") or "Lead" in (lead_data.get("name") or "")):
                lead_data["name"] = session_state["name"]
            # Merge phone from session state (critical for enrichment lookups)
            if session_state.get("phone") and not lead_data.get("phone"):
                lead_data["phone"] = session_state["phone"]
            # Merge email from session state
            if session_state.get("email") and not lead_data.get("email"):
                lead_data["email"] = session_state["email"]
            # Session_state OVERRIDES extracted data for user-selected fields
            # (subjects, grade, goal) because user clicks are authoritative
            for _sk in ("subjects", "grade", "goal"):
                if session_state.get(_sk):
                    lead_data[_sk] = session_state[_sk]  # always override
            # Also override 'course' with user-selected subject so that
            # interested_courses and intent show the correct subject
            if session_state.get("subjects"):
                lead_data["course"] = session_state["subjects"]
            # Other fields: merge only if missing
            for _sk in ("board", "user_type", "preferred_time", "language"):
                if session_state.get(_sk) and not lead_data.get(_sk):
                    lead_data[_sk] = session_state[_sk]

            # If the widget sent an explicit exam_target (UPSC/NEET/JEE/CAT/GMAT),
            # prefer that as the course label instead of session_state subjects.
            if exam_target:
                lead_data["course"] = exam_target

            # ── Safety net: scan conversation history for name if still fallback ──
            if not lead_data.get("name") or "Lead" in (lead_data.get("name") or ""):
                import re as _re2
                _name_ask_re = _re2.compile(
                    r'(what.{0,5}(is|\'s) your (good )?name|share your name|'
                    r'may i (have|know|get) your name|could (you|i) .{0,20}name|'
                    r'tell me your name|name please|can i get your name|get your name)',
                    _re2.IGNORECASE
                )
                for i, msg in enumerate(conversation_history):
                    sender = msg.get("sender") or msg.get("role", "")
                    text_val = msg.get("message") or msg.get("content", "")
                    if sender in ("bot", "assistant") and _name_ask_re.search(text_val):
                        # Check the NEXT message — if it's a user reply that looks like a name
                        if i + 1 < len(conversation_history):
                            next_msg = conversation_history[i + 1]
                            next_sender = next_msg.get("sender") or next_msg.get("role", "")
                            next_text = (next_msg.get("message") or next_msg.get("content", "")).strip()
                            if next_sender in ("user", "human") and _re2.match(r'^[A-Za-z]{2,20}(\s+[A-Za-z]{2,20}){0,2}$', next_text):
                                lead_data["name"] = next_text.title()
                                logger.info(f"🔍 [LEAD-CAPTURE] Name recovered from conversation history: {lead_data['name']}")
                                break

            # Compute lead_temperature from session completeness
            if lead_data.get("name") and lead_data.get("phone") and session_state.get("preferred_time"):
                lead_data["lead_temperature"] = "HOT"
            elif lead_data.get("name") and lead_data.get("phone"):
                lead_data["lead_temperature"] = "WARM"
            else:
                lead_data["lead_temperature"] = "COLD"

            logger.info(
                f"🔍 [LEAD-CAPTURE] Extracted: name={lead_data.get('name')} "
                f"email={lead_data.get('email')} phone={lead_data.get('phone')} "
                f"course={lead_data.get('course')} temp={lead_data.get('lead_temperature')}"
            )

            try:
                from app.models import Lead as LeadModel
                existing = None
                
                # Check for duplicate by phone OR email (check both, not elif)
                if lead_data.get('phone'):
                    existing = db.query(LeadModel).filter(
                        LeadModel.phone == lead_data['phone'],
                        LeadModel.tenant_id == tenant_id
                    ).first()
                if not existing and lead_data.get('email'):
                    existing = db.query(LeadModel).filter(
                        LeadModel.email == lead_data['email'],
                        LeadModel.tenant_id == tenant_id
                    ).first()

                if existing:
                    # ── Enrich existing lead with new data instead of just skipping ──
                    updated_fields = []

                    # Update name if current is a fallback placeholder
                    new_name = lead_data.get('name')
                    is_fallback_name = any(x in (existing.name or '') for x in ['Phone Lead', 'Unknown', 'Lead ('])
                    if new_name and is_fallback_name and 'Lead' not in new_name:
                        existing.name = new_name
                        updated_fields.append(f"name={new_name}")

                    # Fill in email if missing
                    if lead_data.get('email') and not existing.email:
                        existing.email = lead_data['email']
                        updated_fields.append(f"email={lead_data['email']}")

                    # Merge chatbot_context with new enrichment data
                    ctx = existing.chatbot_context or {}
                    # ALWAYS override subjects/grade/goal (authoritative from user clicks)
                    for _ck in ('subjects', 'grade', 'goal'):
                        if lead_data.get(_ck) and ctx.get(_ck) != lead_data[_ck]:
                            ctx[_ck] = lead_data[_ck]
                            updated_fields.append(f"{_ck}={lead_data[_ck]}")
                    # Other fields: fill only if missing
                    for _ck in ('board', 'user_type',
                                'preferred_time', 'language', 'lead_temperature',
                                'exam_target', 'preparation_stage', 'city'):
                        if lead_data.get(_ck) and not ctx.get(_ck):
                            ctx[_ck] = lead_data[_ck]
                            updated_fields.append(f"{_ck}={lead_data[_ck]}")
                    # Recalculate temperature after enrichment
                    _has_name = bool(existing.name and 'Lead' not in existing.name)
                    _has_phone = bool(existing.phone)
                    _has_ptime = bool(ctx.get('preferred_time'))
                    if _has_name and _has_phone and _has_ptime:
                        ctx['lead_temperature'] = 'HOT'
                        if 'lead_temperature=HOT' not in updated_fields:
                            updated_fields.append('lead_temperature=HOT')
                    elif _has_name and _has_phone:
                        ctx['lead_temperature'] = 'WARM'

                    if updated_fields:
                        existing.chatbot_context = ctx
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(existing, 'chatbot_context')
                        db.commit()
                        logger.info(f"🔄 [LEAD-CAPTURE] Enriched existing lead {existing.id}: {', '.join(updated_fields)}")
                    else:
                        logger.info(f"🔍 [LEAD-CAPTURE] Contact already exists as lead {existing.id} — no new data to update")

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

                        # Sia v2.0: Do NOT override the AI response — Sia's confirmation is better
                    else:
                        logger.error(f"🔍 [LEAD-CAPTURE] capture_lead FAILED (returned None)")
            except Exception as e:
                logger.error(f"❌ [LEAD-CAPTURE] Exception: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.info(f"🔍 [LEAD-CAPTURE] No contact info in message or session_state — skipping capture")

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
    Public endpoint for Sia/widget lead capture. Creates a lead without JWT.
    Supports Sia v2.0 enriched fields: grade, board, subjects, goal,
    user_type, preferred_time, language, lead_temperature.
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

        # ── Sia v2.0 enriched fields ─────────────────────────────────
        grade = (body.get("grade") or "").strip() or None
        board = (body.get("board") or "").strip() or None
        subjects = body.get("subjects") or []
        goal = (body.get("goal") or "").strip() or None
        user_type = (body.get("user_type") or "").strip() or None
        preferred_time = (body.get("preferred_time") or "").strip() or None
        language = (body.get("language") or "English").strip()

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

        # ── Compute lead temperature (Sia v2.0 rules) ───────────────
        # HOT: name + phone + preferred_time (all 9 steps done)
        # WARM: name + phone but no preferred_time, OR reached step 6+
        # COLD: only FAQ / browsed 1-3 steps / no personal data
        if name and phone and preferred_time:
            lead_temperature = "HOT"
        elif name and phone:
            lead_temperature = "WARM"
        else:
            lead_temperature = "COLD"

        lead_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "exam_target": exam_target,
            "preparation_stage": preparation_stage,
            "city": city,
            "source": "website_chatbot",
            # Sia v2.0 enrichment
            "grade": grade,
            "board": board,
            "subjects": subjects if isinstance(subjects, list) else [subjects] if subjects else [],
            "goal": goal,
            "user_type": user_type,
            "preferred_time": preferred_time,
            "language": language,
            "lead_temperature": lead_temperature,
        }
        if exam_target:
            lead_data["course"] = exam_target
        elif goal:
            lead_data["course"] = goal

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
            "lead_temperature": lead_temperature,
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


@router.get("/sessions/{session_id}")
async def get_chatbot_session_detail(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed chatbot session including conversation messages."""
    try:
        from app.models.lead import ChatbotSession as CS

        session = None
        # Try by primary key UUID first
        try:
            sid_uuid = uuid.UUID(session_id)
            session = db.query(CS).filter(CS.id == sid_uuid).first()
        except (ValueError, TypeError):
            pass

        # Fallback: try by session_id string column
        if not session:
            session = db.query(CS).filter(CS.session_id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Build conversation list
        conversation = session.conversation or []

        # Get linked lead info if available
        lead_info = None
        if session.lead_id:
            from app.models.lead import Lead as LeadModel
            lead = db.query(LeadModel).filter(LeadModel.id == session.lead_id).first()
            if lead:
                lead_info = {
                    "id": str(lead.id),
                    "name": lead.name,
                    "phone": lead.phone,
                    "email": lead.email,
                    "status": lead.status.value if lead.status else None,
                }

        return {
            "id": str(session.id),
            "session_id": session.session_id,
            "visitor_id": session.session_id,
            "start_time": session.created_at.isoformat() if session.created_at else None,
            "duration": session.duration_seconds or 0,
            "message_count": session.message_count or 0,
            "messages": conversation,
            "lead_captured": session.lead_captured == "true" or session.lead_id is not None,
            "lead": lead_info,
            "status": "completed" if session.lead_captured == "true" else "active",
            "engagement_score": session.engagement_score or 0,
            "intent_detected": session.intent_detected,
            "summary": session.summary,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session detail: {e}", exc_info=True)
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

