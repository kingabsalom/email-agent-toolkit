"""
Daily Digest
Formats the pipeline results as a plain-text summary email and sends it
to the authenticated user's own Gmail address.
"""

import base64
import datetime
import email.mime.text

from gmail_reader import get_service


def _count_by_label(rows: list) -> dict:
    counts = {"urgent": 0, "action-required": 0, "routine": 0, "spam": 0}
    for _, classification, _ in rows:
        label = classification["classification"].lower()
        counts[label] = counts.get(label, 0) + 1
    return counts


def format_digest(rows: list, suggested_subjects: list = None, reminders: list = None) -> str:
    """
    Format priority-sorted pipeline results as a plain-text digest.

    Args:
        rows:               list of (email, classification, priority), sorted by score desc
        suggested_subjects: list of improved subject strings, same order as rows
        reminders:          list of follow-up reminder dicts from followup_tracker

    Returns:
        Plain-text string suitable for an email body
    """
    if suggested_subjects is None:
        suggested_subjects = [""] * len(rows)
    if reminders is None:
        reminders = []

    today  = datetime.date.today().strftime("%A, %B %-d, %Y")
    counts = _count_by_label(rows)

    lines = []
    lines.append(f"EMAIL DIGEST — {today}")
    lines.append(
        f"{len(rows)} emails processed  |  "
        f"{counts['urgent']} urgent  |  "
        f"{counts['action-required']} action-required  |  "
        f"{counts['routine']} routine  |  "
        f"{counts['spam']} spam"
    )
    lines.append("=" * 70)

    # Summary table
    lines.append(f"\n{'#':>2}  {'Score':>5}  {'Classification':<16}  {'Sender':<28}  Subject")
    lines.append("-" * 70)
    for rank, ((email, classification, priority), _) in enumerate(zip(rows, suggested_subjects), 1):
        label   = classification["classification"].upper()
        sender  = email["sender"][:28]
        subject = email["subject"][:30]
        lines.append(f"{rank:>2}  {priority['score']:>2}/10  {label:<16}  {sender:<28}  {subject}")
    lines.append("-" * 70)

    # Detailed section
    lines.append("\n\nDETAILED VIEW\n")
    for rank, ((email, classification, priority), suggested) in enumerate(zip(rows, suggested_subjects), 1):
        label = classification["classification"].upper()
        lines.append(f"{rank}. [{label}  {priority['score']}/10]  {email['sender']}")
        lines.append(f"   Subject: {email['subject']}")
        if suggested and suggested != email["subject"]:
            lines.append(f"   Suggested: {suggested}")
        lines.append(f"   Priority: {priority['explanation']}")
        if classification["action_items"]:
            lines.append("   Action items:")
            for item in classification["action_items"]:
                lines.append(f"     - {item}")
        lines.append("")

    # Follow-up reminders section
    if reminders:
        lines.append("=" * 70)
        lines.append(f"FOLLOW-UP REMINDERS  ({len(reminders)} unanswered)\n")
        for r in reminders:
            lines.append(f"  {r['days_waiting']}d waiting  →  {r['to']}")
            lines.append(f"  Subject: {r['subject']}")
            lines.append(f"  Sent: {r['sent_date']}")
            lines.append("")

    lines.append("=" * 70)
    lines.append("Open your dashboard: http://127.0.0.1:5000")
    lines.append("To launch it: python3 run_dashboard.py")
    lines.append("Sent by email-agent-toolkit")
    return "\n".join(lines)


def send_digest(rows: list, suggested_subjects: list = None, reminders: list = None) -> str:
    """
    Send the formatted digest to the authenticated user's own Gmail address.

    Returns:
        The recipient email address the digest was sent to
    """
    service = get_service()

    profile    = service.users().getProfile(userId="me").execute()
    user_email = profile["emailAddress"]

    today  = datetime.date.today().strftime("%B %-d, %Y")
    counts = _count_by_label(rows)
    subject = (
        f"Email Digest — {today} | "
        f"{len(rows)} emails, {counts['urgent']} urgent"
    )
    if reminders:
        subject += f", {len(reminders)} follow-ups"

    body = format_digest(rows, suggested_subjects, reminders)

    msg          = email.mime.text.MIMEText(body, "plain")
    msg["To"]    = user_email
    msg["From"]  = user_email
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    return user_email
