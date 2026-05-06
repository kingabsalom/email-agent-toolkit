"""
Follow-up Tracker
Scans the SENT folder for emails that have received no reply after a threshold
number of days, surfacing them so nothing falls through the cracks.
"""

import datetime

from gmail_reader import get_service


def get_followup_reminders(threshold_days: int = 3, check_count: int = 30) -> list:
    """
    Find sent emails with no reply after threshold_days.

    Checks the most recent check_count SENT messages and returns any whose
    thread has only one message (the original send) and are older than
    threshold_days.

    Args:
        threshold_days: how many days without reply before flagging (default 3)
        check_count:    how many recent sent messages to inspect (default 30)

    Returns:
        list of dicts with keys: subject, to, sent_date, days_waiting
    """
    service = get_service()

    result = service.users().messages().list(
        userId="me",
        labelIds=["SENT"],
        maxResults=check_count,
    ).execute()

    messages = result.get("messages", [])
    if not messages:
        return []

    now = datetime.datetime.now(datetime.timezone.utc)
    reminders = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "To", "Date"],
        ).execute()

        internal_ms = int(full.get("internalDate", 0))
        sent_at     = datetime.datetime.fromtimestamp(internal_ms / 1000, tz=datetime.timezone.utc)
        days_waiting = (now - sent_at).days

        if days_waiting < threshold_days:
            continue

        thread_id = full["threadId"]
        thread    = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="minimal",
        ).execute()

        # If the thread has more than one message, someone replied
        if len(thread.get("messages", [])) > 1:
            continue

        headers  = full["payload"].get("headers", [])
        subject  = next((h["value"] for h in headers if h["name"].lower() == "subject"), "(no subject)")
        to       = next((h["value"] for h in headers if h["name"].lower() == "to"), "")

        reminders.append({
            "subject":      subject,
            "to":           to,
            "sent_date":    sent_at.strftime("%Y-%m-%d"),
            "days_waiting": days_waiting,
        })

    reminders.sort(key=lambda r: r["days_waiting"], reverse=True)
    return reminders


def print_followup_reminders(reminders: list) -> None:
    """Print follow-up reminders in a compact table."""
    if not reminders:
        print("\nNo follow-up reminders.")
        return

    print(f"\n{'─' * 60}")
    print(f"FOLLOW-UP REMINDERS  ({len(reminders)} unanswered)\n")
    for r in reminders:
        print(f"  {r['days_waiting']}d  {r['to'][:30]:<30}  {r['subject'][:35]}")
    print(f"{'─' * 60}")
