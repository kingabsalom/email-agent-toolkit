"""
Tests for the Flask dashboard routes using Flask's test client.
Pipeline calls are mocked so no real Gmail or Claude API access is needed.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

SAMPLE_DASHBOARD_DATA = {
    "processed_at": "2026-05-06 10:00",
    "emails": [
        {
            "sender":               "boss@company.com",
            "subject":              "Q3 report due Friday",
            "date":                 "Mon, 06 May 2026 09:00:00 +0000",
            "classification":       "action-required",
            "confidence":           0.9,
            "priority_score":       7,
            "priority_explanation": "Deadline this week from manager.",
            "action_items":         ["Send department summary", "Review budget"],
            "suggested_subject":    "Q3 Report: Submission Due Friday 5pm",
            "suggestions": [
                {"label": "Formal",  "subject": "Re: Q3 report due Friday", "body": "Understood, I will send by Thursday."},
                {"label": "Brief",   "subject": "Re: Q3 report due Friday", "body": "On it."},
            ],
            "calendar_event": {
                "is_meeting_request": False,
                "summary": "", "date": "", "time": "",
                "duration_minutes": 30, "timezone": "",
                "attendees": [], "description": "",
            },
        }
    ],
    "followup_reminders": [
        {"subject": "Invoice #42", "to": "vendor@supply.com", "sent_date": "2026-04-30", "days_waiting": 6}
    ],
}


@pytest.fixture
def client(tmp_path):
    """Flask test client with a pre-written dashboard_data.json."""
    data_file = tmp_path / "dashboard_data.json"
    data_file.write_text(json.dumps(SAMPLE_DASHBOARD_DATA))

    import dashboard
    dashboard.DATA_FILE = str(data_file)
    dashboard.app.config["TESTING"] = True
    dashboard.app.secret_key = "test"

    with dashboard.app.test_client() as c:
        yield c, str(data_file)


def test_index_returns_200(client):
    c, _ = client
    resp = c.get("/")
    assert resp.status_code == 200


def test_index_shows_email_subject(client):
    c, _ = client
    resp = c.get("/")
    assert b"Q3 report due Friday" in resp.data


def test_index_shows_followup_banner(client):
    c, _ = client
    resp = c.get("/")
    assert b"Invoice #42" in resp.data


def test_index_shows_action_items(client):
    c, _ = client
    resp = c.get("/")
    assert b"Send department summary" in resp.data


def test_index_shows_suggested_subject(client):
    c, _ = client
    resp = c.get("/")
    assert b"Q3 Report: Submission Due Friday 5pm" in resp.data


def test_save_draft_calls_create_draft(client):
    c, _ = client
    mock_result = {"id": "draft_xyz"}
    with patch("create_draft.create_draft", return_value=mock_result) as mock_cd:
        resp = c.post("/save-draft", data={"email_idx": "0", "draft_idx": "0"})
    assert resp.status_code == 302
    mock_cd.assert_called_once()
    args = mock_cd.call_args.args
    assert "Understood, I will send by Thursday." in args


def test_create_tasks_calls_create_tasks(client):
    c, _ = client
    with patch("create_tasks.create_tasks", return_value=[{"id": "t1", "title": "Task"}]) as mock_ct:
        resp = c.post("/create-tasks", data={"email_idx": "0"})
    assert resp.status_code == 302
    mock_ct.assert_called_once()


def test_create_event_calls_create_calendar_event(client):
    c, data_file = client
    data = json.loads(json.dumps(SAMPLE_DASHBOARD_DATA))
    data["emails"][0]["calendar_event"]["is_meeting_request"] = True
    data["emails"][0]["calendar_event"]["summary"] = "Budget Review"
    with open(data_file, "w") as f:
        json.dump(data, f)

    with patch("create_calendar_event.create_calendar_event", return_value={"id": "evt_1", "html_link": ""}) as mock_ce:
        resp = c.post("/create-event", data={"email_idx": "0"})
    assert resp.status_code == 302
    mock_ce.assert_called_once()
