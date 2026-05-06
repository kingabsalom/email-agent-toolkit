"""
Email Pipeline
Classifies, scores, and suggests responses — sorted by priority.

Uses real Gmail emails if credentials.json is present, otherwise falls back
to sample_emails.json for testing.

Usage:
    python3 main.py
"""

import json
import os
from classify_emails import classify_email, print_summary
from suggest_responses import suggest_responses, print_suggestions
from score_priority import score_priority
from create_draft import create_draft
from export_csv import export_csv
from detect_calendar_event import detect_calendar_event, print_event_details
from create_calendar_event import create_calendar_event
from create_tasks import create_tasks
from followup_tracker import get_followup_reminders, print_followup_reminders
from enrich_contact import enrich_contact


def truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def print_summary_table(rows: list) -> None:
    W = {"rank": 2, "score": 5, "label": 16, "items": 5, "sender": 26, "subject": 32}
    rule_width = sum(W.values()) + len(W) * 2

    header = (
        f"{'#':>{W['rank']}}  "
        f"{'Score':>{W['score']}}  "
        f"{'Classification':<{W['label']}}  "
        f"{'Items':>{W['items']}}  "
        f"{'Sender':<{W['sender']}}  "
        f"Subject"
    )

    print("\nPRIORITY SUMMARY")
    print("─" * rule_width)
    print(header)
    print("─" * rule_width)

    for rank, (email, classification, priority) in enumerate(rows, 1):
        label   = classification["classification"].upper()
        n_items = len(classification["action_items"])
        print(
            f"{rank:>{W['rank']}}  "
            f"{priority['score']:>2}/10  "
            f"{label:<{W['label']}}  "
            f"{n_items:>{W['items']}}  "
            f"{truncate(email['sender'], W['sender']):<{W['sender']}}  "
            f"{truncate(email['subject'], W['subject'])}"
        )

    print("─" * rule_width)


def _prompt_save_draft(email: dict, suggestions: dict) -> str | None:
    """Prompt user to save a suggested reply as a Gmail draft. Returns chosen label or None."""
    opts  = suggestions["suggestions"]
    count = len(opts)
    while True:
        choice = input(f"\n  Save a draft? Enter 1-{count} or s to skip: ").strip().lower()
        if choice == "s":
            return None
        if choice.isdigit() and 1 <= int(choice) <= count:
            selected = opts[int(choice) - 1]
            result   = create_draft(email["sender"], selected["subject"], selected["body"])
            print(f"  Draft saved to Gmail (id: {result['id']})")
            return selected["label"]
        print(f"  Enter a number 1-{count} or 's' to skip.")


def _prompt_create_calendar_event(event: dict) -> bool:
    """Prompt user to create a Google Calendar event. Returns True if created."""
    choice = input("\n  Add to Google Calendar? (y/n): ").strip().lower()
    if choice == "y":
        result = create_calendar_event(event)
        print(f"  Event created: {result['html_link'] or result['id']}")
        return True
    return False


def _prompt_create_tasks(email: dict, action_items: list) -> bool:
    """Prompt user to add action items to Google Tasks. Returns True if created."""
    print(f"\n  {len(action_items)} action item(s) found.")
    choice = input("  Add to Google Tasks? (y/n): ").strip().lower()
    if choice == "y":
        created = create_tasks(action_items, email)
        print(f"  {len(created)} task(s) added to Google Tasks.")
        return True
    return False


def load_emails() -> tuple:
    """
    Load emails from Gmail if credentials.json exists, otherwise use sample data.
    Returns (emails, source_label, using_gmail).
    """
    script_dir       = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(script_dir, "credentials.json")

    if os.path.exists(credentials_path):
        print("credentials.json found — connecting to Gmail...")
        from gmail_reader import read_inbox
        emails = read_inbox(count=10)
        return emails, "Gmail inbox (last 10)", True

    print("No credentials.json found — using sample emails.")
    print("See README for Gmail setup instructions.\n")
    with open(os.path.join(script_dir, "sample_emails.json")) as f:
        return json.load(f), "sample_emails.json", False


def main():
    emails, source, using_gmail = load_emails()

    print(f"Processing {len(emails)} emails from {source}...")

    # Phase 1: enrich, classify, and score every email
    print("Classifying and scoring ", end="", flush=True)
    rows = []
    for email in emails:
        contact        = enrich_contact(email["sender"]) if using_gmail else {}
        classification = classify_email(email)
        priority       = score_priority(email, classification, contact)
        rows.append((email, classification, priority))
        print(".", end="", flush=True)
    print(" done.\n")

    # Phase 2: sort highest priority first
    rows.sort(key=lambda row: row[2]["score"], reverse=True)

    # Phase 3: summary table
    print_summary_table(rows)

    # Phase 4: detailed view with all interactive prompts
    print("\n\nDETAILED VIEW  (sorted by priority)\n")
    draft_choices      = []
    suggested_subjects = []

    for rank, (email, classification, priority) in enumerate(rows, 1):
        print_summary(email, classification)
        print(f"\nPriority: {priority['score']}/10 — {priority['explanation']}")

        # Calendar event detection
        if using_gmail:
            event = detect_calendar_event(email)
            if event["is_meeting_request"]:
                print_event_details(event)
                _prompt_create_calendar_event(event)

        # Task extraction
        if using_gmail and classification["action_items"]:
            _prompt_create_tasks(email, classification["action_items"])

        # Response suggestions
        suggestions = suggest_responses(email, classification)
        print_suggestions(suggestions)
        suggested_subjects.append(suggestions.get("suggested_subject") or "")

        if using_gmail:
            draft_choices.append(_prompt_save_draft(email, suggestions))
        else:
            draft_choices.append(None)

    # Phase 5: follow-up reminders
    if using_gmail:
        print("\nChecking for follow-up reminders...")
        reminders = get_followup_reminders()
        print_followup_reminders(reminders)

    # Phase 6: export to CSV
    csv_path = export_csv(rows, draft_choices, suggested_subjects)
    print(f"\n{'─' * 60}")
    print(f"Results exported to: {csv_path}")
    print("Done.")


if __name__ == "__main__":
    main()
