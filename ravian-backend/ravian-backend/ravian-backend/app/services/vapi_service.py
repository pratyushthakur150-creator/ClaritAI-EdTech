"""
VAPI Voice API integration service.

This service provides a thin async wrapper around the VAPI HTTP API
so that FastAPI routers can initiate outbound voice calls.
"""

import os
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class VAPIService:
    """Service for interacting with the VAPI voice API."""

    def __init__(self) -> None:
        self.api_key: Optional[str] = settings.vapi_api_key
        self.base_url: str = "https://api.vapi.ai"

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("VAPI_API_KEY is not configured in environment")

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        """Ensure phone number is in E.164 format (e.g. +918905538374)."""
        # Strip whitespace and dashes
        phone_number = phone_number.strip().replace("-", "").replace(" ", "")

        if phone_number.startswith("+"):
            return phone_number

        # Starts with country code 91 but no '+' prefix
        if phone_number.startswith("91") and len(phone_number) == 12:
            return "+" + phone_number

        # Just 10 digits – assume India (+91)
        if len(phone_number) == 10 and phone_number.isdigit():
            return "+91" + phone_number

        raise ValueError(
            f"Invalid phone number format: {phone_number}. "
            "Must be E.164 format like +918905538374"
        )

    async def create_outbound_call(
        self,
        phone_number: str,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initiate an outbound phone call via VAPI."""

        if not self.api_key:
            raise ValueError("VAPI API key is not configured")

        # Ensure phone number is in E.164 format
        phone_number = self._normalize_phone_number(phone_number)

        # VAPI outbound call payload (correct format per VAPI API)
        phone_number_id = settings.vapi_phone_number_id or os.environ.get('VAPI_PHONE_NUMBER_ID', '').strip()
        assistant_id_val = assistant_id or settings.vapi_assistant_id
        if not assistant_id_val:
            raise ValueError("VAPI_ASSISTANT_ID or assistant_id parameter is required")

        payload: Dict[str, Any] = {
            "assistantId": assistant_id_val,
            "customer": {
                "number": phone_number,
                "name": metadata.get('student_name', 'Student') if metadata else 'Student'
            }
        }
        if phone_number_id:
            payload["phoneNumberId"] = phone_number_id
        else:
            # Fallback: Twilio integration
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '').strip()
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '').strip()
            twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER', '').strip()
            if twilio_sid and twilio_token and twilio_phone:
                payload['phoneNumber'] = {
                    'twilioPhoneNumber': twilio_phone,
                    'twilioAccountSid': twilio_sid,
                    'twilioAuthToken': twilio_token,
                }
            else:
                raise ValueError(
                    "VAPI outbound calls require either VAPI_PHONE_NUMBER_ID or "
                    "TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_PHONE_NUMBER in .env"
                )

        if metadata:
            payload['assistantOverrides'] = {
                'variableValues': metadata
            }

        logger.info(f"VAPI payload: {payload}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/call",
                headers=self._get_headers(),
                json=payload,
            )

            # Better error handling – surface VAPI's actual error message
            if response.status_code != 200 and response.status_code != 201:
                try:
                    error_detail = response.json()
                except Exception:
                    error_detail = {"error": response.text or "Unknown error"}
                logger.error(
                    f"VAPI API error ({response.status_code}): {error_detail}"
                )
                raise httpx.HTTPStatusError(
                    f"VAPI API returned {response.status_code}: {error_detail}",
                    request=response.request,
                    response=response,
                )

            return response.json()
