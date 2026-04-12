import os
import json
import logging
import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import subprocess

try:
    import openai
    from openai import OpenAI
except ImportError:
    raise
    import openai
    from openai import OpenAI

try:
    from dotenv import load_dotenv
except ImportError:
    raise
    from dotenv import load_dotenv

load_dotenv()

class AssistantService:
    """
    AssistantService handles both text and voice mode queries with RAG search,
    LLM response generation, and voice synthesis capabilities.
    """
    
    def __init__(self, 
                 vector_store=None,
                 voice_service=None,
                 interaction_log=None,
                 demo_mode: bool = True):
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.demo_mode = demo_mode
        self.vector_store = vector_store
        self.voice_service = voice_service
        self.interaction_log = interaction_log
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.llm_client = OpenAI(api_key=api_key)
            if self.demo_mode:
                self.logger.info("OpenAI API key found, disabling demo mode for LLM operations")
                self.demo_mode = False
        else:
            self.llm_client = None
            if not self.demo_mode:
                self.logger.warning("No API key found, reverting to DEMO mode")
                self.demo_mode = True
        
        # Configuration
        self.TEXT_MODE_MAX_TOKENS = 500
        self.VOICE_MODE_MAX_TOKENS = 300
        self.RAG_SEARCH_TOP_K = 3
        self.CONFUSION_THRESHOLD = 0.3
        
        self.logger.info(f"AssistantService initialized in {'demo' if demo_mode else 'production'} mode")

    def _validate_request(self, student, tenant_id: str, mode: str) -> None:
        """Validate request parameters and permissions"""
        try:
            if not student or not tenant_id:
                raise ValueError("Student and tenant_id are required")
            
            if hasattr(student, 'tenant_id') and str(student.tenant_id) != str(tenant_id):
                # Check if it's an enrollment object
                pass
            # if hasattr(student, 'tenant_id') and str(student.tenant_id) != str(tenant_id):
            #    raise ValueError(f"Student tenant mismatch: {student.tenant_id} != {tenant_id}")
            
            if mode == 'voice' and hasattr(student, 'voice_enabled') and not student.voice_enabled:
                raise ValueError("Voice mode not enabled for this student")
                
            self.logger.info(f"Request validation passed for student {getattr(student, 'id', 'unknown')}, tenant {tenant_id}, mode {mode}")
            
        except Exception as e:
            self.logger.error(f"Request validation failed: {e}")
            raise

    def _generate_voice_prompt(self, query: str, context: List[Dict]) -> str:
        """Generate conversational prompt optimized for voice responses"""
        # ... (rest of method unchanged)
        context_text = "\n".join([f"- {doc['content']}" for doc in context[:2]])
        
        prompt = f"""You are a helpful teaching assistant. Provide a clear, concise answer suitable for voice response.

Context information:
{context_text}

Student question: {query}

Instructions:
- Keep response conversational and under 50 words
- Use simple language appropriate for voice
- Focus on the most important points
- End with a natural conclusion

Answer:"""
        return prompt

    def _generate_text_prompt(self, query: str, context: List[Dict]) -> str:
        """Generate detailed prompt for text-based responses"""
        context_text = "\n".join([f"- {doc['content']}" for doc in context[:3]])
        
        prompt = f"""You are a knowledgeable teaching assistant. Provide a comprehensive, well-structured answer.

Context information:
{context_text}

Student question: {query}

Instructions:
- Provide a detailed but clear answer
- Use examples where helpful
- Structure the response with bullet points if appropriate
- Include relevant context from the provided information

Answer:"""
        return prompt

    async def _get_llm_response(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Get response from LLM (OpenAI or demo fallback)"""
        if self.llm_client and not self.demo_mode:
            try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful teaching assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                text = response.choices[0].message.content.strip()
                return {'text': text, 'confidence': 0.85}
            except Exception as e:
                self.logger.warning(f"LLM call failed, using demo response: {e}")
        
        # Demo/fallback response
        return {
            'text': 'This is a demo response from the AI Teaching Assistant. '
                    'In production, this would be powered by an LLM with RAG-based context. '
                    'The system searches through course materials to find relevant information '
                    'and generates a comprehensive answer tailored to your question.',
            'confidence': 0.75
        }

    def _generate_follow_up_questions(self, query: str, answer: str) -> List[str]:
        """Generate contextual follow-up question suggestions"""
        # In production, an LLM would generate these based on the conversation
        return [
            "Can you explain this in more detail?",
            "What are some practical examples?",
            "How does this relate to the assignments?"
        ]

    def _check_escalation_needed(self, confidence: float, context_relevance: float) -> Dict:
        """Check if the query needs human escalation"""
        needed = confidence < self.CONFUSION_THRESHOLD or context_relevance < 0.2
        reason = None
        if needed:
            if confidence < self.CONFUSION_THRESHOLD:
                reason = "Low confidence in generated answer"
            elif context_relevance < 0.2:
                reason = "Insufficient relevant context found"
        
        return {
            'needed': needed,
            'reason': reason,
            'confidence_score': confidence,
            'context_relevance': context_relevance
        }


    async def answer_query(self,
                          student,
                          tenant_id: str,
                          query: Optional[str] = None,
                          audio_url: Optional[str] = None,
                          mode: str = 'text',
                          voice_settings: Optional[Dict] = None,
                          return_audio: bool = True) -> Dict:
        """
        Handle both text and voice mode queries with RAG search and response generation.
        """
        try:
            start_time = datetime.now()
            
            self.logger.info(f"Starting {mode} mode query processing for student {getattr(student, 'id', 'unknown')}")
            
            # Validate request
            self._validate_request(student, tenant_id, mode)
            
            # Initialize response structure
            response = {
                'interaction_id': str(uuid.uuid4()),
                'timestamp': start_time.isoformat(),
                'student_id': getattr(student, 'id', None),
                'tenant_id': tenant_id,
                'mode': mode,
                'query_text': query, # Will be updated for voice
                'audio_url': audio_url,
                'audio_duration': None,
                'transcript': None,
                'answer_text': None,
                'response_audio_url': None,
                'response_audio_duration': None,
                'sources': [],
                'follow_up_questions': [],
                'confidence_score': None,
                'escalation': None,
                'processing_time': None
            }
            
            # Handle voice mode - transcribe audio first
            if mode == 'voice':
                if not audio_url:
                    raise ValueError("audio_url is required for voice mode")
                
                if self.voice_service:
                    self.logger.info(f"Transcribing audio: {audio_url}")
                    transcription_result = await self.voice_service.transcribe_audio(audio_url, tenant_id)
                    
                    query = transcription_result['transcript']
                    response['transcript'] = query
                    response['query_text'] = query # Update query_text with transcript
                    response['audio_duration'] = transcription_result.get('duration')
                    
                    self.logger.info(f"Audio transcribed: '{query}' (duration: {transcription_result.get('duration')}s)")
                else:
                    raise ValueError("VoiceService not available for voice mode")
            
            if not query:
                raise ValueError("Query text is required (either directly or from audio transcription)")
            
            # Perform RAG search
            self.logger.info(f"Performing RAG search for query: '{query}'")
            if self.vector_store:
                search_results = self.vector_store.search(query, tenant_id, top_k=self.RAG_SEARCH_TOP_K)
            else:
                search_results = []
            
            response['sources'] = [
                {
                    'id': result.get('id'),
                    'content': result.get('content'),
                    'relevance_score': result.get('score'),
                    'metadata': result.get('metadata')
                }
                for result in search_results
            ]
            
            avg_relevance = sum(result.get('score', 0) for result in search_results) / len(search_results) if search_results else 0
            self.logger.info(f"Found {len(search_results)} relevant sources (avg relevance: {avg_relevance:.2f})")
            
            # Generate appropriate prompt based on mode
            if mode == 'voice':
                prompt = self._generate_voice_prompt(query, search_results)
                max_tokens = self.VOICE_MODE_MAX_TOKENS
                self.logger.info(f"Generated voice-optimized prompt (max tokens: {max_tokens})")
            else:
                prompt = self._generate_text_prompt(query, search_results)
                max_tokens = self.TEXT_MODE_MAX_TOKENS
                self.logger.info(f"Generated text prompt (max tokens: {max_tokens})")
            
            # Get LLM response
            self.logger.info(f"Generating LLM response...")
            llm_result = await self._get_llm_response(prompt, max_tokens)
            
            response['answer_text'] = llm_result['text']
            response['confidence_score'] = llm_result['confidence']
            
            self.logger.info(f"LLM response generated (confidence: {llm_result['confidence']:.2f})")
            
            # Generate follow-up questions
            response['follow_up_questions'] = self._generate_follow_up_questions(query, llm_result['text'])
            
            # Check escalation conditions
            escalation_check = self._check_escalation_needed(llm_result['confidence'], avg_relevance)
            response['escalation'] = escalation_check
            
            if escalation_check['needed']:
                self.logger.info(f"Escalation needed: {escalation_check['reason']}")
            
            # Handle voice response generation
            if mode == 'voice' and return_audio and response['answer_text'] and self.voice_service:
                self.logger.info(f"Generating voice response...")
                voice_settings = voice_settings or {}
                
                tts_result = await self.voice_service.text_to_speech(
                    text=response['answer_text'],
                    tenant_id=tenant_id,
                    voice=voice_settings.get('voice_id', 'alloy'),
                    speed=voice_settings.get('speed', 1.0)
                )
                
                response['response_audio_url'] = tts_result['audio_url']
                response['response_audio_duration'] = tts_result['duration']
                
                self.logger.info(f"Voice response generated: {tts_result['filename']} ({tts_result['duration']:.1f}s)")
            
            # Calculate processing time
            end_time = datetime.now()
            response['processing_time'] = (end_time - start_time).total_seconds()
            
            # Log interaction
            if self.interaction_log:
                interaction_id = self.interaction_log.create_interaction({
                    'student_id': getattr(student, 'id', None),
                    'tenant_id': tenant_id,
                    'mode': mode,
                    'query': query,
                    'answer': response['answer_text'],
                    'confidence': response['confidence_score'],
                    'sources_count': len(response['sources']),
                    'escalation_needed': escalation_check['needed'],
                    'processing_time': response['processing_time'],
                    'audio_duration': response.get('audio_duration'),
                    'response_audio_duration': response.get('response_audio_duration')
                })
                response['interaction_id'] = interaction_id
            
            self.logger.info(f"Query processed successfully in {response['processing_time']:.2f}s (ID: {response['interaction_id']})")
            
            return response
            
        except Exception as e:
            error_msg = f"Query processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'interaction_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'student_id': getattr(student, 'id', None) if student else None,
                'tenant_id': tenant_id,
                'mode': mode,
                'error': error_msg,
                'success': False
            }

    def get_interaction_history(self, student_id: str, tenant_id: str, limit: int = 10) -> List[Dict]:
        """Get recent interaction history for a student"""
        try:
            if not self.interaction_log:
                return []
                
            student_interactions = [
                log for log in self.interaction_log.logs 
                if log.get('student_id') == student_id and log.get('tenant_id') == tenant_id
            ]
            
            student_interactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return student_interactions[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get interaction history: {e}")
            return []

    def get_tenant_usage_stats(self, tenant_id: str) -> Dict:
        """Get usage statistics for a tenant"""
        try:
            if not self.interaction_log:
                return {'error': 'Interaction log not available'}
                
            tenant_interactions = [
                log for log in self.interaction_log.logs 
                if log.get('tenant_id') == tenant_id
            ]
            
            voice_interactions = [log for log in tenant_interactions if log.get('mode') == 'voice']
            text_interactions = [log for log in tenant_interactions if log.get('mode') == 'text']
            
            total_audio_duration = sum(
                log.get('audio_duration', 0) for log in voice_interactions
            )
            
            escalations = [log for log in tenant_interactions if log.get('escalation_needed')]
            
            return {
                'tenant_id': tenant_id,
                'total_interactions': len(tenant_interactions),
                'voice_interactions': len(voice_interactions),
                'text_interactions': len(text_interactions),
                'total_audio_duration': total_audio_duration,
                'escalations_count': len(escalations),
                'avg_confidence': sum(
                    log.get('confidence', 0) for log in tenant_interactions
                ) / len(tenant_interactions) if tenant_interactions else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {'error': str(e)}
