from __future__ import annotations
import base64
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "gmail_token.json"


def _get_gmail_service():
    creds = None

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(f"credentials.json not found at: {CREDENTIALS_PATH}")

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        flow.oauth2session.params.update({"prompt": "select_account"})
    
        creds = flow.run_local_server(
    port=0,
    authorization_prompt_message="Please open this URL and choose the correct Gmail account.",
    success_message="Authentication complete. You can close this tab.",
    open_browser=True,
)

        with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def list_unread_messages(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Return unread inbox messages.
    """
    service = _get_gmail_service()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q="is:unread in:inbox",
                    maxResults=max_results,
                )
                .execute()
            )
            return response.get("messages", [])
        except HttpError as e:
            if e.resp.status >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Server error ({e.resp.status}), retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise


def get_message(message_id: str) -> Dict[str, Any]:
    """
    Fetch a full Gmail message by ID.
    """
    service = _get_gmail_service()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as e:
            if e.resp.status >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Server error ({e.resp.status}), retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise


def _extract_header(headers: List[Dict[str, str]], name: str) -> str:
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def _decode_base64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")


def extract_plain_text_body(payload: Dict[str, Any]) -> str:
    """
    Extract plain text body from Gmail payload.
    """
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data")
            if mime_type == "text/plain" and body_data:
                return _decode_base64url(body_data)

        # fallback: nested multipart sections
        for part in payload["parts"]:
            if "parts" in part:
                nested = extract_plain_text_body(part)
                if nested:
                    return nested

    body_data = payload.get("body", {}).get("data")
    if body_data:
        return _decode_base64url(body_data)

    return ""


def parse_message(message: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert raw Gmail message into a simpler dict.
    """
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    return {
        "message_id": message.get("id", ""),
        "thread_id": message.get("threadId", ""),
        "from": _extract_header(headers, "From"),
        "subject": _extract_header(headers, "Subject"),
        "body": extract_plain_text_body(payload),
    }


def send_reply(to_email: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a Gmail reply.
    """
    service = _get_gmail_service()

    mime_message = MIMEText(body)
    mime_message["to"] = to_email
    mime_message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")

    request_body: Dict[str, Any] = {"raw": raw_message}
    if thread_id:
        request_body["threadId"] = thread_id

    return (
        service.users()
        .messages()
        .send(userId="me", body=request_body)
        .execute()
    )


def mark_as_read(message_id: str) -> Dict[str, Any]:
    """
    Remove UNREAD label after processing.
    """
    service = _get_gmail_service()

    return (
        service.users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        )
        .execute()
    )