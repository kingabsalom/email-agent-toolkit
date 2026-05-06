from unittest.mock import MagicMock, patch


FULL_EVENT = {
    "is_meeting_request": True,
    "summary": "Budget Review",
    "date": "2026-05-10",
    "time": "14:00",
    "duration_minutes": 30,
    "timezone": "America/New_York",
    "attendees": ["alex@bigclient.com"],
    "description": "Review revised budget.",
}

ALLDAY_EVENT = {**FULL_EVENT, "time": ""}
NO_TZ_EVENT  = {**FULL_EVENT, "timezone": ""}
NO_DATE_EVENT = {**FULL_EVENT, "date": ""}


def _mock_calendar_service(event_id="evt_abc"):
    mock = MagicMock()
    mock.events.return_value.insert.return_value.execute.return_value = {
        "id": event_id,
        "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
    }
    return mock


def test_returns_event_id_and_link():
    from create_calendar_event import create_calendar_event
    with patch("create_calendar_event.get_calendar_service", return_value=_mock_calendar_service()):
        result = create_calendar_event(FULL_EVENT)
    assert result["id"] == "evt_abc"
    assert "html_link" in result


def test_timed_event_uses_datetime_format():
    from create_calendar_event import create_calendar_event
    mock_svc = _mock_calendar_service()
    with patch("create_calendar_event.get_calendar_service", return_value=mock_svc):
        create_calendar_event(FULL_EVENT)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    assert "dateTime" in body["start"]


def test_allday_event_uses_date_format():
    from create_calendar_event import create_calendar_event
    mock_svc = _mock_calendar_service()
    with patch("create_calendar_event.get_calendar_service", return_value=mock_svc):
        create_calendar_event(ALLDAY_EVENT)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    assert "date" in body["start"]
    assert "dateTime" not in body["start"]


def test_attendees_included_when_present():
    from create_calendar_event import create_calendar_event
    mock_svc = _mock_calendar_service()
    with patch("create_calendar_event.get_calendar_service", return_value=mock_svc):
        create_calendar_event(FULL_EVENT)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    assert body["attendees"] == [{"email": "alex@bigclient.com"}]


def test_no_timezone_defaults_to_utc():
    from create_calendar_event import create_calendar_event
    mock_svc = _mock_calendar_service()
    with patch("create_calendar_event.get_calendar_service", return_value=mock_svc):
        create_calendar_event(NO_TZ_EVENT)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    assert body["start"]["timeZone"] == "UTC"


def test_missing_date_defaults_to_today():
    import datetime
    from create_calendar_event import create_calendar_event
    mock_svc = _mock_calendar_service()
    with patch("create_calendar_event.get_calendar_service", return_value=mock_svc):
        create_calendar_event(NO_DATE_EVENT)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    today = datetime.date.today().isoformat()
    assert today in body["start"]["dateTime"]
