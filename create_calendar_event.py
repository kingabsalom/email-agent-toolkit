"""
Calendar Event Creator
Creates a Google Calendar event from detected meeting details.
"""

import datetime

from gmail_reader import get_calendar_service


def create_calendar_event(event_data: dict) -> dict:
    """
    Create a Google Calendar event from detected meeting details.

    Args:
        event_data: dict returned by detect_calendar_event (must have is_meeting_request=True)

    Returns:
        dict with event 'id' and 'html_link'
    """
    service = get_calendar_service()

    tz = event_data.get("timezone") or "UTC"
    date_str = event_data.get("date") or datetime.date.today().isoformat()
    time_str = event_data.get("time") or ""
    duration = event_data.get("duration_minutes") or 30

    if time_str:
        start_dt = f"{date_str}T{time_str}:00"
        end_dt   = _add_minutes(start_dt, duration)
        start    = {"dateTime": start_dt, "timeZone": tz}
        end      = {"dateTime": end_dt,   "timeZone": tz}
    else:
        # No time specified — create an all-day event
        start = {"date": date_str}
        end   = {"date": date_str}

    body = {
        "summary":     event_data.get("summary", "Meeting"),
        "description": event_data.get("description", ""),
        "start":       start,
        "end":         end,
    }

    attendees = event_data.get("attendees", [])
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]

    event = service.events().insert(
        calendarId="primary",
        body=body,
        sendUpdates="none",
    ).execute()

    return {"id": event["id"], "html_link": event.get("htmlLink", "")}


def _add_minutes(dt_str: str, minutes: int) -> str:
    """Add minutes to an ISO datetime string (YYYY-MM-DDTHH:MM:SS)."""
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    dt += datetime.timedelta(minutes=minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
