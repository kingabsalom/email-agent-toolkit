import pytest
from unittest.mock import patch
from tests.conftest import SAMPLE_EMAIL, CLASSIFY_RESPONSE, SUGGEST_RESPONSE, mock_api_response


def _call(payload=None):
    from suggest_responses import suggest_responses
    p = payload or SUGGEST_RESPONSE
    with patch("suggest_responses.client.messages.create", return_value=mock_api_response(p)):
        return suggest_responses(SAMPLE_EMAIL, CLASSIFY_RESPONSE)


def test_returns_suggestions_list():
    result = _call()
    assert "suggestions" in result
    assert isinstance(result["suggestions"], list)


def test_suggestions_have_required_fields():
    result = _call()
    for s in result["suggestions"]:
        assert "label" in s
        assert "subject" in s
        assert "body" in s


def test_subject_starts_with_re():
    result = _call()
    for s in result["suggestions"]:
        assert s["subject"].startswith("Re:")


def test_multiple_suggestions_returned():
    result = _call()
    assert len(result["suggestions"]) >= 2


def test_spam_single_suggestion_allowed():
    spam_classification = {"classification": "spam", "confidence": 0.98, "action_items": []}
    payload = {
        "suggestions": [
            {"label": "Action", "subject": "Re: You won!", "body": "Mark as spam and delete."}
        ]
    }
    from suggest_responses import suggest_responses
    with patch("suggest_responses.client.messages.create", return_value=mock_api_response(payload)):
        result = suggest_responses(SAMPLE_EMAIL, spam_classification)
    assert len(result["suggestions"]) >= 1


def test_bodies_are_nonempty():
    result = _call()
    for s in result["suggestions"]:
        assert len(s["body"].strip()) > 0


def test_suggested_subject_returned():
    result = _call()
    assert "suggested_subject" in result
    assert isinstance(result["suggested_subject"], str)


def test_suggested_subject_nonempty_when_vague():
    payload = {**SUGGEST_RESPONSE, "suggested_subject": "Q3 Budget Review: Approval Needed by Friday"}
    result = _call(payload)
    assert len(result["suggested_subject"]) > 0


def test_suggested_subject_unchanged_when_clear():
    payload = {**SUGGEST_RESPONSE, "suggested_subject": "CRITICAL: Production database down — immediate action needed"}
    result = _call(payload)
    assert result["suggested_subject"] == "CRITICAL: Production database down — immediate action needed"
