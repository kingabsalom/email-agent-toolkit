"""
Dashboard Runner
Processes the Gmail inbox through the full pipeline, saves results to
dashboard_data.json, then launches the Flask web dashboard.

Usage:
    python3 run_dashboard.py
    python3 run_dashboard.py --count 20 --port 8080 --no-browser
"""

import argparse
import datetime
import json
import os
import threading
import webbrowser

from gmail_reader import read_inbox
from classify_emails import classify_email
from score_priority import score_priority
from suggest_responses import suggest_responses
from enrich_contact import enrich_contact
from reputation import get_reputation, record_interaction
from detect_calendar_event import detect_calendar_event
from followup_tracker import get_followup_reminders
from export_csv import export_csv

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.json")


def build_dashboard_data(hours: int = 48) -> dict:
    """
    Run the full pipeline and return a JSON-serializable dict ready for the dashboard.

    Args:
        hours: fetch emails from the last N hours (default: 48)

    Returns:
        dict with 'processed_at', 'emails', and 'followup_reminders'
    """
    emails = read_inbox(count=500, query=f"newer_than:{hours}h")

    print(f"Processing {len(emails)} emails from the last {hours}h ", end="", flush=True)
    rows               = []
    suggested_subjects = []
    email_records      = []

    for email in emails:
        contact        = enrich_contact(email["sender"])
        reputation     = get_reputation(email["sender"])
        classification = classify_email(email)
        priority       = score_priority(email, classification, contact, reputation)
        suggestions    = suggest_responses(email, classification)
        event          = detect_calendar_event(email)

        record_interaction(email["sender"])

        rows.append((email, classification, priority))
        suggested_subject = suggestions.get("suggested_subject") or ""
        suggested_subjects.append(suggested_subject)

        email_records.append({
            "sender":               email["sender"],
            "subject":              email["subject"],
            "date":                 email.get("date", ""),
            "classification":       classification["classification"],
            "confidence":           classification["confidence"],
            "priority_score":       priority["score"],
            "priority_explanation": priority["explanation"],
            "action_items":         classification["action_items"],
            "suggested_subject":    suggested_subject,
            "suggestions":          suggestions["suggestions"],
            "calendar_event":       event,
        })
        print(".", end="", flush=True)
    print(" done.")

    rows.sort(key=lambda r: r[2]["score"], reverse=True)
    email_records.sort(key=lambda e: e["priority_score"], reverse=True)

    print("Checking follow-up reminders...")
    reminders = get_followup_reminders()

    # Save CSV log
    csv_path = export_csv(rows, [None] * len(rows), suggested_subjects)
    print(f"CSV saved: {csv_path}")

    return {
        "processed_at":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "emails":            email_records,
        "followup_reminders": reminders,
    }


def main():
    parser = argparse.ArgumentParser(description="Process inbox and launch the web dashboard.")
    parser.add_argument("--hours",      type=int,  default=48,    help="Hours of email history to process (default: 48)")
    parser.add_argument("--port",       type=int,  default=5000,  help="Flask port (default: 5000)")
    parser.add_argument("--no-browser", action="store_true",      help="Don't open browser automatically")
    args = parser.parse_args()

    data = build_dashboard_data(hours=args.hours)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

    url = f"http://127.0.0.1:{args.port}"
    print(f"\nDashboard ready at {url} (opening browser...)")

    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    from dashboard import app
    app.run(debug=False, port=args.port)


if __name__ == "__main__":
    main()
