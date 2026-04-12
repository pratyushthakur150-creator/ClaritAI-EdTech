import os
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from groq import Groq as GroqClient
except ImportError:
    GroqClient = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

GROQ_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")

class VoiceService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Groq client for Whisper transcription
        groq_key = os.getenv('GROQ_API_KEY')
        if GroqClient and groq_key:
            self._groq_client = GroqClient(api_key=groq_key)
            self.logger.info(f"VoiceService: Groq Whisper client initialized (model={GROQ_WHISPER_MODEL})")
        else:
            self._groq_client = None
            self.logger.warning("VoiceService: GROQ_API_KEY not set — transcription unavailable")

        # OpenAI client for TTS only
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.logger.info("VoiceService initialized with OpenAI TTS client")
        else:
            self.client = None
            self.logger.warning("VoiceService initialized WITHOUT OpenAI client (TTS demo mode only)")
            
    async def transcribe_audio(self, file_path: str, tenant_id: str, language: str = None) -> Dict:
        """Transcribe audio file using Groq Whisper API"""
        start_time = datetime.now()

        if not self._groq_client:
            return {
                'transcript': "Transcription unavailable: GROQ_API_KEY not configured.",
                'confidence': 1.0,
                'duration': 0.0,
                'language': language or 'en',
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'tenant_id': tenant_id,
                'timestamp': start_time.isoformat()
            }

        try:
            with open(file_path, "rb") as audio_file:
                transcript_response = self._groq_client.audio.transcriptions.create(
                    file=(Path(file_path).name, audio_file.read()),
                    model=GROQ_WHISPER_MODEL,
                    language=language or "en",
                    response_format="verbose_json"
                )

            transcript_text = transcript_response.text

            return {
                'transcript': transcript_text,
                'confidence': 1.0,
                'duration': getattr(transcript_response, 'duration', 0.0),
                'language': getattr(transcript_response, 'language', language or 'en'),
                'file_size': os.path.getsize(file_path),
                'tenant_id': tenant_id,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise

    async def text_to_speech(self, text: str, tenant_id: str, voice: str = 'alloy', speed: float = 1.0) -> Dict:
        """Convert text to speech using OpenAI TTS"""
        if not self.client:
             return {
                'audio_url': None,
                'filename': None,
                'duration': 0,
                'file_size': 0,
                'voice_id': voice,
                'speed': speed,
                'text_length': len(text),
                'tenant_id': tenant_id,
                'timestamp': datetime.now().isoformat()
            }

        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed
            )
            
            # Save file to uploads/audio_responses/{tenant_id}
            base_dir = Path(os.getcwd())
            output_dir = base_dir / "uploads" / "audio_responses" / tenant_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            file_path = output_dir / filename
            
            response.stream_to_file(file_path)
            
            return {
                'audio_url': f"/api/v1/voice/audio/{tenant_id}/{filename}",
                'filename': filename,
                'duration': len(text) / 15.0, # Estimate
                'file_size': os.path.getsize(file_path),
                'voice_id': voice,
                'speed': speed,
                'text_length': len(text),
                'tenant_id': tenant_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"TTS failed: {e}")
            raise
