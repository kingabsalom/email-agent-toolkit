"""Shared fixtures and helpers for the test suite."""

import json
from unittest.mock import MagicMock


SAMPLE_EMAIL = {
    "sender": "boss@company.com",
    "subject": "Production outage",
    "body": "The prod DB is down. Fix it now.",
    "date": "Mon, 05 May 2026 09:00:00 +0000",
}


def mock_api_response(json_payload: dict) -> MagicMock:
    """Return a MagicMock that looks like an Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=json.dumps(json_payload))]
    return mock


CLASSIFY_RESPONSE = {
    "classification": "urgent",
    "confidence": 0.97,
    "action_items": ["Fix the production database immediately"],
}

SCORE_RESPONSE = {
    "score": 9,
    "explanation": "Critical outage with immediate deadline from a senior sender.",
}

SUGGEST_RESPONSE = {
    "suggested_subject": "Production DB Outage: 5k Users Affected — Active Incident",
    "suggestions": [
        {
            "label": "Formal",
            "subject": "Re: Production outage",
            "body": "Acknowledged. I am investigating the issue now.",
        },
        {
            "label": "Brief",
            "subject": "Re: Production outage",
            "body": "On it.",
        },
    ]
}
