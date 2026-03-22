from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dateutil import parser as date_parser
from dateutil.tz import gettz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# level of access required for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_service():
    """
    Authenticate the user with Google Calendar and return a Calendar API service client.

    First run:
    - Opens browser for OAuth consent
    - Saves token.json locally

    Later runs:
    - Reuses token.json if still valid
    """
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _parse_datetime(
    date_text: str,
    time_text: str,
    timezone_name: str = "America/Los_Angeles",
) -> datetime:
    """
    Convert natural-ish date/time strings into a timezone-aware datetime.

    Example inputs:
    - date_text='tomorrow'
    - time_text='3pm'
    """
    tzinfo = gettz(timezone_name)
    now = datetime.now(tzinfo)

    combined = f"{date_text} {time_text}".strip()

    # dateutil can parse many standard forms, but not plain 'tomorrow'.
    # Handle a few common relative cases manually first.
    lowered = combined.lower()

    if "tomorrow" in lowered:
        parsed_time = date_parser.parse(time_text, default=now)
        target_date = now.date() + timedelta(days=1)
        dt = datetime.combine(target_date, parsed_time.time(), tzinfo=tzinfo)
        return dt

    if "today" in lowered:
        parsed_time = date_parser.parse(time_text, default=now)
        dt = datetime.combine(now.date(), parsed_time.time(), tzinfo=tzinfo)
        return dt

    dt = date_parser.parse(combined, default=now)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzinfo)

    return dt


def check_availability(
    start_dt: datetime,
    end_dt: datetime,
    calendar_id: str = "primary",
) -> bool:
    """
    Check whether the user's calendar is free in the requested time window.

    Returns True if free, False if busy.
    """
    service = _get_calendar_service()

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": "America/Los_Angeles",
        "items": [{"id": calendar_id}],
    }

    result = service.freebusy().query(body=body).execute()
    busy_slots = result["calendars"][calendar_id]["busy"]

    return len(busy_slots) == 0


def create_meeting_event(
    summary: str,
    start_dt: datetime,
    end_dt: datetime,
    attendee_email: Optional[str] = None,
    description: str = "",
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """
    Create a Google Calendar event and request a Google Meet link.

    Returns the created event resource.
    """
    service = _get_calendar_service()

    event_body: Dict[str, Any] = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "America/Los_Angeles",
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"meet-{int(datetime.now().timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    if attendee_email:
        event_body["attendees"] = [{"email": attendee_email}]

    event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        )
        .execute()
    )

    return event


def extract_meeting_link(event: Dict[str, Any]) -> str:
    """
    Extract the Google Meet link from the created event if available.
    """
    return event.get("hangoutLink", "")