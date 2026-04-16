"""
Chatbot Service for AI-powered lead generation chatbot
"""
import logging
import re
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func, desc

from app.models import ChatbotSession, Lead, LeadSource, LeadStatus, UrgencyLevel, Tenant, User, UserRole
from app.core.config import settings
from app.services.intent_recognition import intent_service
from app.services.intent_classifier import intent_classifier

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for chatbot operations"""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_tenant_exists(self, tenant_id: UUID) -> UUID:
        """Ensure a tenant row exists in the DB before creating sessions.
        If the tenant_id is missing, create a default tenant AND a bot user."""
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            return tenant.id

        # Auto-create a default tenant so the FK constraint is satisfied
        logger.info(f"Auto-creating tenant {tenant_id} for chatbot session")
        tenant = Tenant(
            id=tenant_id,
            name="Chatbot Default Org",
            domain=f"chatbot-{str(tenant_id)[:8]}.ravian.com",
        )
        self.db.add(tenant)
        self.db.flush()  # flush so ID is usable immediately

        # Also create a bot/system user so Lead.created_by can reference it
        from app.core.auth import hash_password
        bot_user = User(
            tenant_id=tenant.id,
            email=f"bot@chatbot-{str(tenant_id)[:8]}.ravian.com",
            password_hash=hash_password(str(uuid4())),  # random password, not usable
            first_name="Chatbot",
            last_name="Bot",
            role=UserRole.ADMIN,
            is_active=True,  # Fixed: Boolean field
        )
        self.db.add(bot_user)
        self.db.flush()
        logger.info(f"Created bot user {bot_user.id} for tenant {tenant_id}")

        return tenant.id

    def create_session(
        self,
        tenant_id: UUID,
        visitor_id: Optional[str] = None,
        lead_id: Optional[UUID] = None,
        initial_message: Optional[str] = None
    ) -> ChatbotSession:
        """Create a new chatbot session"""
        try:
            # Ensure tenant exists first to avoid FK violation
            self._ensure_tenant_exists(tenant_id)

            session_id = visitor_id or str(uuid4())
            conversation = []

            if initial_message:
                conversation.append({
                    "sender": "user",
                    "message": initial_message,
                    "timestamp": datetime.utcnow().isoformat()
                })

            session = ChatbotSession(
                tenant_id=tenant_id,
                session_id=session_id,
                lead_id=lead_id,
                conversation=conversation,
                message_count=len(conversation),
                engagement_score=len(conversation)
            )

            try:
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
            except Exception as e:
                self.db.rollback()
                # Session already exists, fetch existing one
                existing = self.db.query(ChatbotSession).filter(
                    ChatbotSession.session_id == session.session_id,
                    ChatbotSession.tenant_id == tenant_id,
                ).first()
                if existing:
                    return existing
                raise e

            logger.info(f"Created chatbot session {session.id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating chatbot session: {str(e)}")
            raise

    def get_session(self, session_id: UUID, tenant_id: UUID) -> Optional[ChatbotSession]:
        """Get chatbot session by ID with tenant isolation"""
        return (
            self.db.query(ChatbotSession)
            .filter(
                ChatbotSession.id == session_id,
                ChatbotSession.tenant_id == tenant_id,
            )
            .first()
        )

    def get_session_by_visitor_id(self, visitor_id: str, tenant_id: UUID) -> Optional[ChatbotSession]:
        """Get chatbot session by visitor_id (string)"""
        return (
            self.db.query(ChatbotSession)
            .filter(
                ChatbotSession.session_id == visitor_id,
                ChatbotSession.tenant_id == tenant_id,
            )
            .first()
        )

    def send_message(
        self,
        session_id: UUID,
        message: str,
        sender: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Add message to conversation"""
        try:
            session = self.get_session(session_id, tenant_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            message_obj = {
                "sender": sender,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            if not session.conversation:
                session.conversation = []

            session.conversation = session.conversation + [message_obj]
            flag_modified(session, 'conversation')
            session.message_count = len(session.conversation)

            response: Dict[str, Any] = {"message": message_obj}

            self.db.commit()
            self.db.refresh(session)

            return response

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def capture_lead(
        self,
        lead_data: dict,
        tenant_id: UUID,
        session_id: str
    ) -> Optional[UUID]:
        """Create lead in database with duplicate check.
        lead_data may include: name, email, phone, course, exam_target, preparation_stage, city.
        """
        try:
            # Check if lead already exists (by email or phone)
            existing_lead = None
            if lead_data.get('email'):
                existing_lead = self.db.query(Lead).filter(
                    Lead.email == lead_data['email'],
                    Lead.tenant_id == tenant_id,
                    Lead.is_deleted == False
                ).first()
            if not existing_lead and lead_data.get('phone'):
                existing_lead = self.db.query(Lead).filter(
                    Lead.phone == lead_data.get('phone'),
                    Lead.tenant_id == tenant_id,
                    Lead.is_deleted == False
                ).first()
            
            if existing_lead:
                return existing_lead.id
            
            # Find system user (or create one) for created_by
            system_user = (
                self.db.query(User)
                .filter(User.tenant_id == tenant_id)
                .first()
            )
            
            if not system_user:
                # Fallback: create bot user
                from app.core.auth import hash_password
                system_user = User(
                    tenant_id=tenant_id,
                    email=f"bot@chatbot-{str(tenant_id)[:8]}.ravian.com",
                    password_hash=hash_password(str(uuid4())),
                    first_name="Chatbot",
                    last_name="Bot",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                self.db.add(system_user)
                self.db.flush()

            # Get chatbot session if session_id is provided
            chatbot_session = None
            if session_id:
                try:
                    chatbot_session = self.db.query(ChatbotSession).filter(
                        ChatbotSession.session_id == session_id,
                        ChatbotSession.tenant_id == tenant_id
                    ).first()
                except Exception as e:
                    logger.warning(f"Could not find chatbot session {session_id}: {e}")
            
            # Build intent and interested_courses from course/exam_target
            course_or_exam = lead_data.get('course') or lead_data.get('exam_target') or 'Website Chatbot'
            intent_parts = [f"Exam/interest: {course_or_exam}"]
            if lead_data.get('preparation_stage'):
                intent_parts.append(f"Stage: {lead_data['preparation_stage']}")
            if lead_data.get('city'):
                intent_parts.append(f"City: {lead_data['city']}")
            intent_str = "; ".join(intent_parts)
            interested_courses = [course_or_exam] if course_or_exam and course_or_exam != 'Website Chatbot' else ['Chatbot inquiry']

            # Chatbot context for Aria/widget: session_id, exam_target, preparation_stage, city, source
            chatbot_ctx = {
                "session_id": str(session_id),
                "source": lead_data.get("source", "website_chatbot"),
            }
            if lead_data.get("exam_target"):
                chatbot_ctx["exam_target"] = lead_data["exam_target"]
            if lead_data.get("preparation_stage"):
                chatbot_ctx["preparation_stage"] = lead_data["preparation_stage"]
            if lead_data.get("city"):
                chatbot_ctx["city"] = lead_data["city"]

            # Lead score from exam_target + preparation_stage (production architecture)
            engagement_score, conversion_probability = self._compute_lead_score(
                lead_data.get("exam_target"),
                lead_data.get("preparation_stage"),
            )

            # Create new lead
            new_lead = Lead(
                tenant_id=tenant_id,
                name=lead_data.get('name', 'Unknown'),
                email=lead_data.get('email'),
                phone=lead_data.get('phone'),
                source=LeadSource.CHATBOT,
                status=LeadStatus.NEW,  # Use enum instead of string
                urgency=UrgencyLevel.MEDIUM,  # Use enum with default
                intent=intent_str,
                interested_courses=interested_courses,
                notes=f'Lead captured from chatbot session: {session_id}',
                created_by=system_user.id,
                chatbot_context=chatbot_ctx,
                chatbot_session_id=chatbot_session.id if chatbot_session else None,
                engagement_score=engagement_score,
                conversion_probability=conversion_probability,
            )
            
            self.db.add(new_lead)
            self.db.commit()
            self.db.refresh(new_lead)
            
            logger.info(f"Captured lead {new_lead.id} from session {session_id}")
            return new_lead.id
            
        except Exception as e:
            logger.error(f"Error capturing lead: {e}", exc_info=True)
            self.db.rollback()
            return None

    def get_stats(self, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get basic chatbot statistics"""
        try:
            base_q = self.db.query(ChatbotSession)
            if tenant_id:
                base_q = base_q.filter(ChatbotSession.tenant_id == tenant_id)

            total_sessions = base_q.count()

            active_sessions = (
                base_q.filter(ChatbotSession.lead_captured == "false").count()
            )

            leads_captured = (
                base_q.filter(
                    ChatbotSession.lead_id.isnot(None),
                ).count()
            )

            avg_duration_q = (
                self.db.query(func.avg(ChatbotSession.duration_seconds))
                .filter(ChatbotSession.duration_seconds.isnot(None))
            )
            if tenant_id:
                avg_duration_q = avg_duration_q.filter(ChatbotSession.tenant_id == tenant_id)
            avg_duration = avg_duration_q.scalar() or 0

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "leads_captured": leads_captured,
                "messages_today": total_sessions,
                "avg_response_time": 0,
                "avg_duration": int(avg_duration),
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "leads_captured": 0,
                "messages_today": 0,
                "avg_response_time": 0,
                "avg_duration": 0,
                "status": "active",
            }

    def get_sessions(self, tenant_id: Optional[UUID] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chatbot sessions from DB."""
        try:
            q = self.db.query(ChatbotSession).order_by(desc(ChatbotSession.created_at))
            if tenant_id:
                q = q.filter(ChatbotSession.tenant_id == tenant_id)
            sessions = q.limit(limit).all()

            return [
                {
                    "id": str(s.id),
                    "visitor_id": s.session_id,
                    "start_time": s.created_at.isoformat() if s.created_at else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "duration": s.duration_seconds or 0,
                    "messages": s.message_count or 0,
                    "lead_captured": s.lead_captured == "true" or s.lead_id is not None,
                    "status": "completed" if s.lead_captured == "true" else "active",
                    "engagement_score": s.engagement_score or 0,
                }
                for s in sessions
            ]
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []

    def extract_lead_info(self, message: str, conversation: list) -> dict:
        """Extract lead information from message and conversation history"""
        lead_data = {
            'name': None,
            'email': None,
            'phone': None,
            'course': None
        }
        
        # Combine recent messages for context
        recent_text = ' '.join([msg.get('message', '') for msg in conversation[-5:]])
        full_text = recent_text + ' ' + message
        
        # Extract email – prefer the CURRENT message, then fall back to history
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, message, re.IGNORECASE) or \
                      re.search(email_pattern, full_text, re.IGNORECASE)
        if email_match:
            lead_data['email'] = email_match.group(1)
        
        # Extract phone – prefer current message first
        # Indian mobile: optional +91 prefix, then 10 digits starting with 6-9
        indian_phone = r'(?:\+?91[\s\-]?)?([6-9]\d{9})'
        # Generic international: 10+ digit number with optional + prefix
        generic_phone = r'(\+?\d[\d\s\-()]{9,})'
        
        phone_match = re.search(indian_phone, message) or \
                      re.search(generic_phone, message) or \
                      re.search(indian_phone, full_text) or \
                      re.search(generic_phone, full_text)
        if phone_match:
            phone_clean = re.sub(r'[^\d+]', '', phone_match.group(1))
            if len(phone_clean) >= 10:
                lead_data['phone'] = phone_clean
        
        # Extract name (multiple patterns — case-insensitive)
        name_patterns = [
            r'name[:\-\s]+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)*)',
            r"i'?m\s+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)*)",
            r'i\s+am\s+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)*)',
            r'this is\s+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)*)',
            r'my name is\s+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)*)',
            r'([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*)?)\s*[,;\s]+[\w.+-]+@', # Name before email
        ]
        
        # When searching for a name, prefer to look around the text that actually
        # contains the chosen email, so we don't accidentally pick an older lead.
        base_text = message
        if lead_data['email'] and lead_data['email'] not in message:
            base_text = full_text

        for pattern in name_patterns:
            name_match = re.search(pattern, base_text, re.IGNORECASE)
            if name_match:
                # Title-case the extracted name for consistency
                lead_data['name'] = name_match.group(1).strip().title()
                break

        # Fallback: if user typed "name email ..." in one line (common in widget),
        # infer the name from the token(s) immediately before the email.
        if not lead_data['name'] and lead_data['email']:
            try:
                search_text = message if lead_data['email'] in message else full_text
                email_idx = search_text.lower().find(lead_data['email'].lower())
                if email_idx > 0:
                    prefix = search_text[:email_idx].strip()
                    # Take last 1-3 words before the email as the name
                    words = [w for w in re.split(r'\s+', prefix) if w]
                    if words:
                        candidate = ' '.join(words[-3:]).strip()
                        # Remove punctuation-only candidates
                        candidate = re.sub(r'^[^A-Za-z]+|[^A-Za-z]+$', '', candidate)
                        if candidate:
                            lead_data['name'] = candidate
            except Exception:
                pass

        # Final fallback: derive a readable name from email local-part
        if not lead_data['name'] and lead_data['email']:
            local_part = lead_data['email'].split('@', 1)[0]
            local_part = re.sub(r'[_\\-.]+', ' ', local_part).strip()
            lead_data['name'] = (local_part[:1].upper() + local_part[1:]) if local_part else 'Website Lead'
        
        # If no name but phone is available, set a fallback name
        if not lead_data['name'] and lead_data['phone'] and not lead_data['email']:
            lead_data['name'] = f'Phone Lead ({lead_data["phone"][-4:]})'
        
        # Extract course interest — only from USER messages, not bot listings
        # Sorted longest-first so "full stack" matches before "stack", etc.
        course_keywords = [
            ('full stack', 'Full Stack Web Dev (MERN)'),
            ('mern', 'Full Stack Web Dev (MERN)'),
            ('web dev', 'Full Stack Web Dev (MERN)'),
            ('digital marketing', 'Digital Marketing'),
            ('marketing', 'Digital Marketing'),
            ('data science', 'Data Science & AI'),
            ('machine learning', 'Data Science & AI'),
            ('python', 'Python Programming'),
            ('ml', 'Data Science & AI'),
            ('ai', 'Data Science & AI'),
        ]

        # Build text from USER messages only (exclude bot replies)
        user_msgs = ' '.join([
            msg.get('message', '') for msg in conversation
            if msg.get('sender') == 'user'
        ])

        # Check current message first, then user history
        for source in [message.lower(), user_msgs.lower()]:
            for keyword, course_name in course_keywords:
                if keyword in source:
                    lead_data['course'] = course_name
                    break
            if lead_data['course']:
                break
        
        return lead_data

    def _compute_lead_score(
        self,
        exam_target: Optional[str],
        preparation_stage: Optional[str],
    ) -> tuple:
        """Set lead_score (engagement_score, conversion_probability) from exam + stage. 0-100."""
        score = 50  # base
        if exam_target and str(exam_target).strip().upper() in ("UPSC", "NEET", "JEE", "CAT", "GMAT"):
            score += 15
        stage = (preparation_stage or "").strip().lower()
        if "appearing this year" in stage or "dropper" in stage:
            score += 20
        elif "preparing" in stage or "1+" in stage:
            score += 10
        elif "just starting" in stage:
            score += 5
        engagement = min(100, max(0, score))
        conversion = min(100, max(0, engagement + 5))  # slight nudge for conversion
        return engagement, conversion

    async def generate_ai_response(
        self,
        message: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-powered response for a chatbot message.

        - Detects intent using IntentRecognitionService
        - Uses OpenAI (when configured) with conversation + context
        - Falls back to simple rule-based responses when AI is unavailable

        Returns:
            {
                "response": str,
                "intent": Dict,
                "should_capture_lead": bool,
            }
        """
        conversation_history = conversation_history or []
        context = context or []

        # Detect intent (production classifier or legacy)
        exam_context_from_request = None
        for item in (context or []):
            c = (item.get("content") or "").lower()
            if "exam" in c or "targeting" in c:
                for ex in ("UPSC", "NEET", "JEE", "CAT", "GMAT"):
                    if ex.lower() in c:
                        exam_context_from_request = ex
                        break
                break

        if getattr(settings, "use_production_intent_classifier", False):
            try:
                prod = await intent_classifier.classify(
                    message=message,
                    conversation_history=conversation_history,
                    exam_context=exam_context_from_request,
                )
                intent_data = {
                    "intent": prod.get("intent", "RANDOM_CHAT"),
                    "confidence": prod.get("confidence", 0.5),
                    "entities": {"exam_context": prod.get("exam_context")},
                }
            except Exception as e:
                logger.warning(f"Production intent classifier failed: {e}, using legacy")
                intent_data = await intent_service.detect_intent(
                    message=message,
                    conversation_history=conversation_history,
                )
        else:
            intent_data = await intent_service.detect_intent(
                message=message,
                conversation_history=conversation_history,
            )

        # Load session to determine lead state / message count
        session: Optional[ChatbotSession] = (
            self.db.query(ChatbotSession)
            .filter(ChatbotSession.session_id == session_id)
            .first()
        )

        message_count = session.message_count if session and session.message_count is not None else 0
        lead_captured_flag = False
        if session:
            lead_captured_flag = bool(
                getattr(session, "lead_id", None) is not None
                or getattr(session, "lead_captured", "") == "true"
            )

        should_capture_lead = self.should_capture_lead(message)
        
        # If lead already captured, don't ask again
        if lead_captured_flag:
            should_capture_lead = False

        # Delay lead capture — require at least 3 messages before prompting
        # unless the user explicitly asks to be contacted
        if should_capture_lead and message_count < 3:
            explicit_contact_words = ['contact me', 'call me', 'reach out', 'sign up', 'signup', 'enroll', 'register']
            if not any(w in message.lower() for w in explicit_contact_words):
                should_capture_lead = False
                logger.info(f"Lead capture suppressed: only {message_count} messages so far")

        # If no OpenAI client / key, use fallback response
        api_key = getattr(settings, "chatbot_api_key", None) or getattr(
            settings, "openai_api_key", None
        )
        if OpenAI is None or not api_key:
            fallback_text = self._rule_based_response(message, intent_data, message_count)
            return {
                "response": fallback_text,
                "intent": intent_data,
                "should_capture_lead": should_capture_lead,
            }

        try:
            client = OpenAI(api_key=api_key)

            # ── RAG: Retrieve exam knowledge and build Aria prompt ────
            # Extract exam_target and preparation_stage from context list
            _exam_target = None
            _prep_stage = None
            for item in (context or []):
                c = (item.get("content") or "")
                if "targeting" in c.lower() or "exam" in c.lower():
                    for ex in ("UPSC", "NEET", "JEE", "CAT", "GMAT"):
                        if ex.lower() in c.lower():
                            _exam_target = ex
                            break
                if "stage" in c.lower() or "preparation" in c.lower():
                    # Extract stage text after "Preparation stage:"
                    import re as _re
                    _stage_match = _re.search(r'(?:Preparation stage|stage)[:\s]+([^.]+)', c, _re.IGNORECASE)
                    if _stage_match:
                        _prep_stage = _stage_match.group(1).strip()

            try:
                from app.rag.chatbot_rag.chatbot_retriever import retrieve_exam_context
                from app.rag.chatbot_rag.context_builder import (
                    build_rag_context, build_chatbot_system_prompt,
                    detect_cross_exam_query, build_sssi_system_prompt, SSSI_TENANT_ID
                )

                # ── SSSi tenant: use SSSi knowledge collection ───────
                _is_sssi = tenant_id and str(tenant_id) == SSSI_TENANT_ID

                if _is_sssi:
                    retrieved_chunks = await retrieve_exam_context(
                        query=message,
                        exam_target="SSSI",
                        top_k=4,
                    )
                    rag_context = build_rag_context(retrieved_chunks)
                    system_prompt = build_sssi_system_prompt(
                        message_count=message_count,
                        rag_context=rag_context,
                    )
                    logger.info(
                        f"[SSSi RAG] chunks={len(retrieved_chunks)}, "
                        f"context_len={len(rag_context)}, msg_count={message_count}"
                    )
                else:
                    # Detect if user is asking about a different exam
                    _cross_exam_detected = None
                    _rag_exam_target = _exam_target
                    detected_exam, is_cross = detect_cross_exam_query(message, _exam_target)
                    if is_cross and detected_exam:
                        _cross_exam_detected = detected_exam
                        _rag_exam_target = detected_exam
                        logger.info(f"Cross-exam detected: target={_exam_target}, asked_about={detected_exam}")

                    retrieved_chunks = await retrieve_exam_context(
                        query=message,
                        exam_target=_rag_exam_target,
                        top_k=3,
                    )
                    rag_context = build_rag_context(retrieved_chunks)
                    system_prompt = build_chatbot_system_prompt(
                        exam_target=_exam_target,
                        preparation_stage=_prep_stage,
                        rag_context=rag_context,
                        cross_exam_detected=_cross_exam_detected,
                        message_count=message_count,
                    )
                    logger.info(
                        f"RAG prompt built: exam={_exam_target}, rag_target={_rag_exam_target}, "
                        f"cross_exam={_cross_exam_detected}, chunks={len(retrieved_chunks)}, "
                        f"context_len={len(rag_context)}, msg_count={message_count}"
                    )
            except Exception as rag_err:
                logger.warning(f"RAG retrieval failed, using fallback prompt: {rag_err}")
                system_prompt = self._build_system_prompt(context, intent_data)

            # Build conversation messages
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": system_prompt}
            ]

            # Add conversation history: last 5 messages only (cost control; never full history)
            email_re = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
            recent = conversation_history[-5:]
            for msg in recent:
                role = msg.get("role") or ("assistant" if msg.get("sender") == "bot" else "user")
                content = msg.get("content") or msg.get("message") or ""
                if content and not email_re.search(content):
                    messages.append({"role": role, "content": content})

            # Current user message
            messages.append({"role": "user", "content": message})

            # Call OpenAI (no max_tokens — use full context window)
            response = client.chat.completions.create(
                model=getattr(settings, "chatbot_model", "gpt-4o-mini"),
                messages=messages,
                temperature=getattr(settings, "chatbot_temperature", 0.7),
            )

            ai_text = response.choices[0].message.content

            return {
                "response": ai_text,
                "intent": intent_data,
                "should_capture_lead": should_capture_lead,
            }

        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"AI response generation failed, using fallback: {e}")
            fallback_text = self._rule_based_response(message, intent_data, message_count)
            return {
                "response": fallback_text,
                "intent": intent_data,
                "should_capture_lead": should_capture_lead,
            }

    def _build_system_prompt(
        self,
        context: Optional[List[Dict[str, Any]]] = None,
        intent_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build an EdTech-specific system prompt with optional context and intent hints.
        This is the FALLBACK prompt used when RAG/context_builder is unavailable."""
        base_prompt = """You are Aria, a helpful AI Academic Advisor for a premium coaching institute.

YOUR APPROACH: Provide genuine value first, then naturally guide toward connecting with a counselor.

FLOW:
1. Answer the student's question helpfully and accurately (3-5 sentences)
2. End with a relevant follow-up question to keep the conversation going
3. After 2-3 helpful exchanges, gently suggest a counselor can provide a personalized study plan
4. After 2-3 helpful exchanges, you may naturally ask for the student's name, WhatsApp number, and email address IN THE CONVERSATION to connect them with a counselor and schedule a session

RULES:
- If the student asks about fees, give whatever information you have — do NOT deflect
- Be warm, encouraging, and empathetic
- Focus on competitive exams: UPSC, JEE, NEET, CAT/MBA, GMAT
- If asked something outside your domain, say you specialize in competitive exam guidance

Available exams: UPSC, JEE, NEET, CAT/MBA, GMAT."""

        # Add detected intent hint
        if intent_data and intent_data.get("intent"):
            base_prompt += f"\n\nDetected intent: {intent_data.get('intent')}"

        # Add context documents
        if context:
            base_prompt += "\n\nRelevant context:\n"
            for item in context[:5]:
                name = item.get("name") or item.get("title") or "Context"
                content = item.get("content") or ""
                base_prompt += f"- {name}: {content}\n"

        return base_prompt

    def _rule_based_response(
        self,
        message: str,
        intent_data: Optional[Dict[str, Any]] = None,
        message_count: int = 0,
    ) -> str:
        """Context-aware rule-based fallback response when AI is unavailable."""
        text = message.lower().strip()

        # Greeting
        if any(w in text for w in ["hello", "hi", "hey", "hii", "hiii"]):
            return "Hello! Welcome to our learning platform. What would you like to learn about today?"

        # Intent-specific responses
        if intent_data:
            intent = intent_data.get("intent")
            if intent == "course_inquiry":
                return "We offer a range of courses including data science, web development, digital marketing, and more. Which subject or skill are you most interested in?"
            if intent == "pricing_question":
                return "Our pricing depends on the course and format. Self-paced courses start at $99, while live mentorship programs range from $199–$499. Which format interests you?"
            if intent == "demo_request":
                return "I'd be happy to help you with a demo! Could you share your name and email so our team can schedule one?"
            if intent == "enrollment_help":
                return "I can guide you through enrollment. Are you already logged into the platform, or would you like to start from the course catalog?"

        # Keyword-based responses
        if any(w in text for w in ["price", "cost", "fee", "cheap", "expensive", "afford"]):
            return "We have flexible pricing options! Self-paced courses start at $99, while mentored programs offer more support at $199–$499. Would you like details on a specific course?"

        if any(w in text for w in ["python", "java", "javascript", "programming", "coding"]):
            return "Great choice! We have beginner, intermediate, and advanced programming courses. Would you like to hear about our Python, JavaScript, or full-stack tracks?"

        if any(w in text for w in ["data science", "machine learning", "ai", "artificial intelligence"]):
            return "We offer comprehensive data science and AI courses covering Python, ML algorithms, deep learning, and real-world projects. Should I share the curriculum details?"

        if any(w in text for w in ["self-paced", "self paced", "difference", "live", "mentor"]):
            return "Self-paced courses let you learn at your own speed with recorded content ($99–$199). Live mentorship programs include weekly sessions with industry experts ($299–$499). Which style suits you better?"

        if any(w in text for w in ["phone", "call", "contact", "representative", "speak"]):
            return "I'd be happy to connect you with a counselor! Could you share your name and phone number? Our team will reach out within 24 hours."

        if any(w in text for w in ["name", "email", "@"]):
            return "Thank you for sharing your details! I've noted them. Our team will reach out to you soon. Is there anything else you'd like to know about our courses?"

        if any(w in text for w in ["no", "nope", "not"]):
            return "No worries! If you change your mind or have other questions, I'm always here to help. Is there anything else I can assist you with?"

        if any(w in text for w in ["yes", "sure", "ok", "okay", "yeah"]):
            return "Could you tell me which subject area interests you? We have courses in programming, data science, digital marketing, design, and more."

        if any(w in text for w in ["thank", "thanks", "bye", "goodbye"]):
            return "You're welcome! Feel free to come back anytime. We're here to help you find the perfect course. Good luck with your learning journey! 🎓"

        # Varied fallback based on conversation stage
        if message_count <= 2:
            return "Thanks for your interest! Could you tell me what subject you'd like to learn about? We have a wide range of courses available."
        elif message_count <= 5:
            return "I'd love to help you find the right course! Could you share more about your learning goals or the specific skill you want to develop?"
        elif message_count <= 8:
            return "To give you the best recommendation, could you share your name and email? That way our team can also send you a detailed course brochure."
        else:
            return "It sounds like you're really interested! Would you like to schedule a free consultation with one of our education advisors? Just share your name and contact info."

    def should_capture_lead(self, message: str) -> bool:
        """Detect if user explicitly wants to submit lead / be contacted.
        
        Removed 'interested' — too many false positives
        (e.g., 'I'm interested in knowing the syllabus' triggers lead capture).
        """
        intent_keywords = [
            'capture', 'lead', 'register', 'sign up', 'signup',
            'enroll', 'join', 'contact me',
            'call me', 'reach out', 'my details', 'my information',
            'counselor', 'counseling', 'free session',
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in intent_keywords)

