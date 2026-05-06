"""
Gmail Reader + Google Auth
Authenticates with Google OAuth2 and provides service builders for Gmail,
Calendar, and Tasks APIs.

Setup (one-time):
  1. Go to console.cloud.google.com
  2. Create a project → Enable the Gmail, Calendar, and Tasks APIs
  3. Create OAuth2 credentials (Desktop app) → Download as credentials.json
  4. Place credentials.json in this directory
  5. Run main.py — a browser window will open to authorize access
  6. token.pickle is saved automatically for future runs
"""

import os
import pickle
import base64
import re
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
TOKEN_FILE       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.pickle")

MAX_BODY_CHARS = 2000


def _get_credentials():
    """Authenticate and return credentials covering all required scopes."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    scope_ok = creds and set(SCOPES).issubset(creds.scopes or set())

    if not creds or not scope_ok:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    elif creds.expired and creds.refresh_token:
        creds.refresh(Request())

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    return creds


def get_service():
    """Return an authenticated Gmail API service."""
    return build("gmail", "v1", credentials=_get_credentials())


def get_calendar_service():
    """Return an authenticated Google Calendar API service."""
    return build("calendar", "v3", credentials=_get_credentials())


def get_tasks_service():
    """Return an authenticated Google Tasks API service."""
    return build("tasks", "v1", credentials=_get_credentials())


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_body(payload: dict) -> str:
    """
    Recursively pull the best plain-text body from a Gmail message payload.
    Gmail messages can be simple (single part) or nested multipart structures.
    """
    mime = payload.get("mimeType", "")

    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace").strip()

    if mime.startswith("multipart/"):
        parts = payload.get("parts", [])

        for part in parts:
            if part.get("mimeType") == "text/plain":
                result = _extract_body(part)
                if result:
                    return result

        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                result = _extract_body(part)
                if result:
                    return result

        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", html).strip()

    return "(no readable body)"


def read_inbox(count: int = 10, query: str = "") -> list:
    """
    Fetch emails from the Gmail inbox.

    Args:
        count: max number of emails to retrieve
        query: optional Gmail search query (e.g. "newer_than:48h")

    Returns list of dicts with keys: sender, subject, body, date
    (same structure as sample_emails.json so agents work unchanged)
    """
    service = get_service()

    kwargs = {"userId": "me", "labelIds": ["INBOX"], "maxResults": count}
    if query:
        kwargs["q"] = query

    result = service.users().messages().list(**kwargs).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = full["payload"].get("headers", [])
        body    = _extract_body(full["payload"])

        emails.append({
            "sender":  _get_header(headers, "From"),
            "subject": _get_header(headers, "Subject") or "(no subject)",
            "body":    body[:MAX_BODY_CHARS],
            "date":    _get_header(headers, "Date"),
        })

    return emails
