"""
Sender Reputation
Tracks interaction history with senders and computes a reputation signal
used to adjust priority scoring over time.

Results are stored in reputation.json and accumulate across sessions.
"""

import datetime
import json
import os
import re

REPUTATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reputation.json")


def _extract_email(sender: str) -> str:
    match = re.search(r"<([^>]+)>", sender)
    return match.group(1).strip().lower() if match else sender.strip().lower()


def _load_db() -> dict:
    if os.path.exists(REPUTATION_FILE):
        try:
            with open(REPUTATION_FILE) as f:
                content = f.read().strip()
            return json.loads(content) if content else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_db(db: dict) -> None:
    with open(REPUTATION_FILE, "w") as f:
        json.dump(db, f, indent=2)


def record_interaction(sender: str, responded: bool = False) -> None:
    """
    Record a received email and optionally a response.

    Args:
        sender:    raw From header value
        responded: True if a draft was saved for this email
    """
    email_addr = _extract_email(sender)
    db  = _load_db()
    now = datetime.datetime.now().isoformat(timespec="seconds")

    if email_addr not in db:
        db[email_addr] = {
            "total_received":  0,
            "total_responded": 0,
            "last_seen":       None,
            "last_responded":  None,
            "created_at":      now,
        }

    entry = db[email_addr]
    entry["total_received"] += 1
    entry["last_seen"] = now

    if responded:
        entry["total_responded"] += 1
        entry["last_responded"] = now

    db[email_addr] = entry
    _save_db(db)


def get_reputation(sender: str) -> dict:
    """
    Return reputation data for a sender.

    Returns:
        dict with response_rate (float|None), total_received (int),
        is_frequent (bool), is_responsive (bool)
    """
    email_addr = _extract_email(sender)
    db    = _load_db()
    entry = db.get(email_addr)

    if not entry or entry["total_received"] == 0:
        return {
            "response_rate":  None,
            "total_received": 0,
            "is_frequent":    False,
            "is_responsive":  False,
        }

    total_received  = entry["total_received"]
    total_responded = entry["total_responded"]
    response_rate   = total_responded / total_received

    return {
        "response_rate":  round(response_rate, 2),
        "total_received": total_received,
        "is_frequent":    total_received >= 5,
        "is_responsive":  response_rate >= 0.5,
    }


def update_from_session(rows: list, draft_choices: list) -> None:
    """
    Record all emails processed in a session.
    Marks responded=True for any email where a draft was saved.
    """
    for (email, _, _), draft_label in zip(rows, draft_choices):
        record_interaction(email["sender"], responded=bool(draft_label))
