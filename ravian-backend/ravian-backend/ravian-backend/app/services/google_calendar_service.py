"""
Google Calendar Service — creates, updates, and deletes calendar events
for demo scheduling with optional Google Meet conferencing.

Requires:
  pip install google-api-python-client google-auth
  
Environment variables:
  GOOGLE_CALENDAR_CREDENTIALS_FILE — path to service account JSON key
  GOOGLE_CALENDAR_ID — calendar to create events on (default: "primary")
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Manages Google Calendar events for demo scheduling."""

    def __init__(self, credentials_file: Optional[str] = None, calendar_id: Optional[str] = None):
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self._service = None
        self._available = False

        if not self.credentials_file:
            logger.warning("Google Calendar credentials file not configured — calendar integration disabled")
            return

        if not os.path.exists(self.credentials_file):
            logger.warning(f"Google Calendar credentials file not found: {self.credentials_file}")
            return

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/calendar"]
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self._service = build("calendar", "v3", credentials=credentials)
            self._available = True
            logger.info(f"Google Calendar service initialized | calendar={self.calendar_id}")
        except ImportError:
            logger.warning("google-api-python-client or google-auth not installed — calendar integration disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")

    @property
    def is_available(self) -> bool:
        return self._available and self._service is not None

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 60,
        description: str = "",
        attendee_emails: Optional[List[str]] = None,
        timezone: str = "Asia/Kolkata",
        add_meet: bool = False,
    ) -> Optional[Dict]:
        """
        Create a Google Calendar event with optional Google Meet link.

        Returns:
            Dict with 'event_id', 'meet_link', 'html_link' or None on failure.
        """
        if not self.is_available:
            logger.debug("Calendar service not available, skipping event creation")
            return None

        try:
            end_time = start_time + timedelta(minutes=duration_minutes)

            event_body = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone,
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 60},
                        {"method": "popup", "minutes": 15},
                    ],
                },
            }

            # Add attendees
            if attendee_emails:
                event_body["attendees"] = [{"email": e} for e in attendee_emails]

            # Add Google Meet conferencing
            conference_version = None
            if add_meet:
                import uuid
                event_body["conferenceData"] = {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                }
                conference_version = 1

            created_event = (
                self._service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=event_body,
                    conferenceDataVersion=conference_version,
                    sendUpdates="all",  # Send email invites to attendees
                )
                .execute()
            )

            event_id = created_event.get("id")
            html_link = created_event.get("htmlLink")

            # Extract Meet link
            meet_link = None
            conference_data = created_event.get("conferenceData", {})
            entry_points = conference_data.get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    meet_link = ep.get("uri")
                    break

            logger.info(f"Created Google Calendar event: {event_id} | meet={bool(meet_link)}")

            return {
                "event_id": event_id,
                "meet_link": meet_link,
                "html_link": html_link,
            }

        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return None

    def update_event(
        self,
        event_id: str,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        timezone: str = "Asia/Kolkata",
    ) -> bool:
        """
        Update an existing Google Calendar event.

        Returns:
            True on success, False on failure.
        """
        if not self.is_available or not event_id:
            return False

        try:
            # Get existing event
            event = (
                self._service.events()
                .get(calendarId=self.calendar_id, eventId=event_id)
                .execute()
            )

            if start_time:
                end_time = start_time + timedelta(minutes=duration_minutes)
                event["start"] = {"dateTime": start_time.isoformat(), "timeZone": timezone}
                event["end"] = {"dateTime": end_time.isoformat(), "timeZone": timezone}

            if summary:
                event["summary"] = summary
            if description is not None:
                event["description"] = description

            self._service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates="all",
            ).execute()

            logger.info(f"Updated Google Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Google Calendar event {event_id}: {e}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """
        Delete (cancel) a Google Calendar event.

        Returns:
            True on success, False on failure.
        """
        if not self.is_available or not event_id:
            return False

        try:
            self._service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates="all",
            ).execute()

            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event {event_id}: {e}")
            return False


# Singleton instance — initialized lazily
_calendar_service: Optional[GoogleCalendarService] = None


def get_calendar_service() -> GoogleCalendarService:
    """Get or create the singleton GoogleCalendarService."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarService()
    return _calendar_service
