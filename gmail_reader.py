"""
Gmail Reader
Authenticates with Google OAuth2 and reads emails from the inbox.

Setup (one-time):
  1. Go to console.cloud.google.com
  2. Create a project → Enable the Gmail API
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
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
TOKEN_FILE       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.pickle")

# Truncate bodies to keep token usage reasonable for the AI agents
MAX_BODY_CHARS = 2000


def get_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Re-run OAuth if creds are missing or don't cover all required scopes
    scope_ok = creds and set(SCOPES).issubset(creds.scopes or set())

    if not creds or not scope_ok:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    elif creds.expired and creds.refresh_token:
        creds.refresh(Request())

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def _get_header(headers: list, name: str) -> str:
    """Find a header value by name (case-insensitive)."""
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

    # Plain text — decode and return directly
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace").strip()

    if mime.startswith("multipart/"):
        parts = payload.get("parts", [])

        # Prefer text/plain over everything else
        for part in parts:
            if part.get("mimeType") == "text/plain":
                result = _extract_body(part)
                if result:
                    return result

        # Recurse into nested multipart blocks (e.g. multipart/alternative inside multipart/mixed)
        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                result = _extract_body(part)
                if result:
                    return result

        # Fall back to HTML, stripping tags
        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", html).strip()

    return "(no readable body)"


def read_inbox(count: int = 10) -> list:
    """
    Fetch the most recent emails from Gmail inbox.

    Args:
        count: how many emails to retrieve (default 10)

    Returns:
        list of dicts with keys: sender, subject, body, date
        (same structure as sample_emails.json so the agents work unchanged)
    """
    service = get_service()

    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=count
    ).execute()

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
