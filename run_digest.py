"""
Daily Digest Runner
Non-interactive entry point designed for cron or launchd.

Fetches the inbox, runs the full pipeline, checks for follow-up reminders,
sends a digest email to yourself, and saves a CSV log.

Usage:
    python3 run_digest.py
    python3 run_digest.py --count 20
"""

import argparse

from gmail_reader import read_inbox
from classify_emails import classify_email
from score_priority import score_priority
from suggest_responses import suggest_responses
from enrich_contact import enrich_contact
from reputation import get_reputation, update_from_session
from followup_tracker import get_followup_reminders
from digest_email import send_digest
from export_csv import export_csv


def main():
    parser = argparse.ArgumentParser(description="Send a daily email digest.")
    parser.add_argument("--count", type=int, default=10, help="Number of emails to process (default: 10)")
    args = parser.parse_args()

    print(f"Fetching {args.count} emails from Gmail...")
    emails = read_inbox(count=args.count)

    print(f"Processing {len(emails)} emails ", end="", flush=True)
    rows               = []
    suggested_subjects = []

    for email in emails:
        contact        = enrich_contact(email["sender"])
        reputation     = get_reputation(email["sender"])
        classification = classify_email(email)
        priority       = score_priority(email, classification, contact, reputation)
        suggestions    = suggest_responses(email, classification)
        rows.append((email, classification, priority))
        suggested_subjects.append(suggestions.get("suggested_subject") or "")
        print(".", end="", flush=True)
    print(" done.")

    rows.sort(key=lambda r: r[2]["score"], reverse=True)
    update_from_session(rows, [None] * len(rows))

    print("Checking follow-up reminders...")
    reminders = get_followup_reminders()

    recipient = send_digest(rows, suggested_subjects, reminders)
    print(f"Digest sent to {recipient}")

    csv_path = export_csv(rows, [None] * len(rows), suggested_subjects)
    print(f"CSV saved:    {csv_path}")


if __name__ == "__main__":
    main()
