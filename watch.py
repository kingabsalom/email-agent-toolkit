"""
Real-time Email Watcher
Polls Gmail via the history API for new inbox messages and processes each
one immediately through the full pipeline.

Does not require Google Cloud Pub/Sub — uses Gmail's historyId to detect
changes since the last poll, so no public endpoint is needed.

Usage:
    python3 watch.py                      # poll every 5 minutes
    python3 watch.py --interval 120       # poll every 2 minutes
    python3 watch.py --interval 60 --count 1  # process 1 email max per poll
"""

import argparse
import datetime
import time

from gmail_reader import get_service, _get_header, _extract_body, MAX_BODY_CHARS
from classify_emails import classify_email, print_summary
from score_priority import score_priority
from suggest_responses import suggest_responses, print_suggestions
from enrich_contact import enrich_contact
from reputation import get_reputation, record_interaction
from detect_calendar_event import detect_calendar_event, print_event_details


def _get_history_id() -> str:
    """Return the current Gmail historyId (a cursor into the mailbox change log)."""
    service = get_service()
    return service.users().getProfile(userId="me").execute()["historyId"]


def _poll_new_messages(since_history_id: str) -> tuple:
    """
    Return (new_message_ids, latest_history_id) since the given historyId.
    Returns ([], since_history_id) if nothing changed or on API error.
    """
    service = get_service()
    try:
        result = service.users().history().list(
            userId="me",
            startHistoryId=since_history_id,
            historyTypes=["messageAdded"],
            labelId="INBOX",
        ).execute()
    except Exception:
        return [], since_history_id

    new_ids = []
    for record in result.get("history", []):
        for added in record.get("messagesAdded", []):
            new_ids.append(added["message"]["id"])

    latest_id = result.get("historyId", since_history_id)
    return new_ids, latest_id


def _fetch_email(msg_id: str) -> dict:
    """Fetch and parse a single Gmail message into the standard email dict."""
    service = get_service()
    full    = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = full["payload"].get("headers", [])
    body    = _extract_body(full["payload"])
    return {
        "sender":  _get_header(headers, "From"),
        "subject": _get_header(headers, "Subject") or "(no subject)",
        "body":    body[:MAX_BODY_CHARS],
        "date":    _get_header(headers, "Date"),
    }


def _process_email(email: dict) -> None:
    """Run the full pipeline for a single new email and print results."""
    contact        = enrich_contact(email["sender"])
    reputation     = get_reputation(email["sender"])
    classification = classify_email(email)
    priority       = score_priority(email, classification, contact, reputation)

    record_interaction(email["sender"])

    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n{'=' * 60}")
    print(f"NEW EMAIL  {now}")
    print(f"{'=' * 60}")
    print_summary(email, classification)
    print(f"\nPriority: {priority['score']}/10 — {priority['explanation']}")

    event = detect_calendar_event(email)
    if event["is_meeting_request"]:
        print_event_details(event)

    suggestions = suggest_responses(email, classification)
    print_suggestions(suggestions)
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Watch Gmail inbox for new emails in real-time.")
    parser.add_argument("--interval", type=int, default=300,
                        help="Poll interval in seconds (default: 300)")
    args = parser.parse_args()

    print(f"Watching Gmail inbox — polling every {args.interval}s. Press Ctrl+C to stop.\n")
    history_id = _get_history_id()
    print(f"Listening from history ID: {history_id}\n")

    while True:
        time.sleep(args.interval)

        timestamp  = datetime.datetime.now().strftime("%H:%M")
        new_ids, history_id = _poll_new_messages(history_id)

        if new_ids:
            print(f"  {timestamp}  {len(new_ids)} new email(s) — processing...", flush=True)
            for msg_id in new_ids:
                email = _fetch_email(msg_id)
                _process_email(email)
        else:
            print(f"  {timestamp}  No new emails.", flush=True)


if __name__ == "__main__":
    main()
