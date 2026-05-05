"""
Draft Creator
Saves a suggested reply as a native Gmail draft via the Gmail API.
"""

import base64
import email.mime.text

from gmail_reader import get_service


def create_draft(to_address: str, subject: str, body: str) -> dict:
    """
    Push a suggested reply to Gmail as a draft.

    Args:
        to_address: recipient (should be the original sender's address)
        subject:    subject line, e.g. "Re: Original Subject"
        body:       plain-text body of the reply

    Returns:
        dict with 'id' (draft ID) and 'message_id' (underlying message ID)
    """
    service = get_service()

    msg = email.mime.text.MIMEText(body, "plain")
    msg["To"] = to_address
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}}
    ).execute()

    return {"id": draft["id"], "message_id": draft["message"]["id"]}
