from unittest.mock import patch
from tests.conftest import SAMPLE_EMAIL, mock_api_response

MEETING_RESPONSE = {
    "is_meeting_request": True,
    "summary": "Budget Review Meeting",
    "date": "2026-05-10",
    "time": "14:00",
    "duration_minutes": 30,
    "timezone": "America/New_York",
    "attendees": ["alex@bigclient.com"],
    "description": "Align on the revised budget.",
}

NO_MEETING_RESPONSE = {
    "is_meeting_request": False,
    "summary": "",
    "date": "",
    "time": "",
    "duration_minutes": 30,
    "timezone": "",
    "attendees": [],
    "description": "",
}


def _call(payload):
    from detect_calendar_event import detect_calendar_event
    with patch("detect_calendar_event.client.messages.create", return_value=mock_api_response(payload)):
        return detect_calendar_event(SAMPLE_EMAIL)


def test_meeting_detected():
    result = _call(MEETING_RESPONSE)
    assert result["is_meeting_request"] is True


def test_non_meeting_returns_false():
    result = _call(NO_MEETING_RESPONSE)
    assert result["is_meeting_request"] is False


def test_meeting_has_summary():
    result = _call(MEETING_RESPONSE)
    assert len(result["summary"]) > 0


def test_meeting_has_date():
    result = _call(MEETING_RESPONSE)
    assert result["date"] == "2026-05-10"


def test_meeting_has_duration():
    result = _call(MEETING_RESPONSE)
    assert isinstance(result["duration_minutes"], int)
    assert result["duration_minutes"] > 0


def test_attendees_is_list():
    result = _call(MEETING_RESPONSE)
    assert isinstance(result["attendees"], list)


def test_no_meeting_attendees_empty():
    result = _call(NO_MEETING_RESPONSE)
    assert result["attendees"] == []
