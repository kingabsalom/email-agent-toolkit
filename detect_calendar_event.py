"""
Calendar Event Detector
Uses Claude to identify meeting requests in emails and extract scheduling details.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a meeting detection assistant. Analyze the email and determine if it contains
a meeting request, scheduling proposal, or calendar invite.

If it does, extract:
- summary: a concise meeting title
- date: the proposed date in YYYY-MM-DD format, or empty string if not specified
- time: the proposed start time in HH:MM 24-hour format, or empty string if not specified
- duration_minutes: estimated duration (default 30 if not mentioned)
- timezone: IANA timezone name if mentioned (e.g. "America/New_York"), or empty string
- attendees: list of email addresses mentioned as participants
- description: 1-2 sentence summary of the meeting purpose drawn from the email

If the email does NOT contain a meeting request, set is_meeting_request to false
and leave all other fields as empty strings or defaults."""

SCHEMA = {
    "type": "object",
    "properties": {
        "is_meeting_request": {"type": "boolean"},
        "summary":            {"type": "string"},
        "date":               {"type": "string"},
        "time":               {"type": "string"},
        "duration_minutes":   {"type": "integer"},
        "timezone":           {"type": "string"},
        "attendees":          {"type": "array", "items": {"type": "string"}},
        "description":        {"type": "string"},
    },
    "required": [
        "is_meeting_request", "summary", "date", "time",
        "duration_minutes", "timezone", "attendees", "description"
    ],
    "additionalProperties": False,
}


def detect_calendar_event(email: dict) -> dict:
    """
    Detect whether an email contains a meeting request and extract details.

    Args:
        email: dict with sender, subject, body

    Returns:
        dict with is_meeting_request (bool) and scheduling fields
    """
    prompt = (
        f"From: {email['sender']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)


def print_event_details(event: dict) -> None:
    """Print detected meeting details."""
    if not event["is_meeting_request"]:
        return
    print("\n  Meeting detected:")
    print(f"    Title:    {event['summary']}")
    if event["date"]:
        time_str = f" at {event['time']}" if event["time"] else ""
        tz_str   = f" ({event['timezone']})" if event["timezone"] else ""
        print(f"    When:     {event['date']}{time_str}{tz_str}")
    print(f"    Duration: {event['duration_minutes']} min")
    if event["attendees"]:
        print(f"    Guests:   {', '.join(event['attendees'])}")
    if event["description"]:
        print(f"    Context:  {event['description']}")
