"""
Web Dashboard
Flask app that displays the priority-sorted inbox and lets you save drafts,
create calendar events, and add tasks — all from the browser.

Reads pipeline results from dashboard_data.json (written by run_dashboard.py).

Usage:
    python3 run_dashboard.py          # process inbox + open dashboard
    python3 dashboard.py              # open dashboard with existing data only
"""

import json
import os

from flask import Flask, flash, redirect, render_template, request, url_for

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.json")

app = Flask(__name__)
app.secret_key = os.urandom(24)


def _load_data():
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def index():
    return render_template("index.html", data=_load_data())


@app.route("/refresh", methods=["POST"])
def refresh():
    """Re-run the full pipeline and reload the dashboard."""
    from run_dashboard import build_dashboard_data
    try:
        data = build_dashboard_data()
        _save_data(data)
        flash(f"Inbox refreshed — {len(data['emails'])} emails processed.", "success")
    except Exception as e:
        flash(f"Refresh failed: {e}", "error")
    return redirect(url_for("index"))


@app.route("/save-draft", methods=["POST"])
def save_draft():
    """Save the selected draft reply to Gmail."""
    from create_draft import create_draft
    data      = _load_data()
    email_idx = int(request.form["email_idx"])
    draft_idx = int(request.form["draft_idx"])

    try:
        email_data = data["emails"][email_idx]
        draft      = email_data["suggestions"][draft_idx]
        result     = create_draft(email_data["sender"], draft["subject"], draft["body"])
        flash(f"Draft saved to Gmail (id: {result['id']}).", "success")
    except Exception as e:
        flash(f"Failed to save draft: {e}", "error")

    return redirect(url_for("index"))


@app.route("/create-event", methods=["POST"])
def create_event():
    """Create a Google Calendar event from a detected meeting."""
    from create_calendar_event import create_calendar_event
    data      = _load_data()
    email_idx = int(request.form["email_idx"])

    try:
        event_data = data["emails"][email_idx]["calendar_event"]
        result     = create_calendar_event(event_data)
        flash(f"Calendar event created.", "success")
    except Exception as e:
        flash(f"Failed to create event: {e}", "error")

    return redirect(url_for("index"))


@app.route("/create-tasks", methods=["POST"])
def create_task():
    """Add action items from an email to Google Tasks."""
    from create_tasks import create_tasks
    data      = _load_data()
    email_idx = int(request.form["email_idx"])

    try:
        email_data   = data["emails"][email_idx]
        action_items = email_data["action_items"]
        email_dict   = {"sender": email_data["sender"], "subject": email_data["subject"]}
        created      = create_tasks(action_items, email_dict)
        flash(f"{len(created)} task(s) added to Google Tasks.", "success")
    except Exception as e:
        flash(f"Failed to create tasks: {e}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False, port=5000)
