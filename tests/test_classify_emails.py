import pytest
from unittest.mock import patch
from tests.conftest import SAMPLE_EMAIL, mock_api_response

VALID_CLASSIFICATIONS = {"urgent", "action-required", "routine", "spam"}


def _call(payload):
    from classify_emails import classify_email
    with patch("classify_emails.client.messages.create", return_value=mock_api_response(payload)):
        return classify_email(SAMPLE_EMAIL)


def test_returns_valid_classification():
    result = _call({"classification": "urgent", "confidence": 0.9, "action_items": []})
    assert result["classification"] in VALID_CLASSIFICATIONS


def test_returns_confidence_between_0_and_1():
    result = _call({"classification": "routine", "confidence": 0.75, "action_items": []})
    assert 0.0 <= result["confidence"] <= 1.0


def test_action_items_is_a_list():
    result = _call({"classification": "action-required", "confidence": 0.8, "action_items": ["Reply by Friday"]})
    assert isinstance(result["action_items"], list)


def test_empty_action_items_for_spam():
    result = _call({"classification": "spam", "confidence": 0.99, "action_items": []})
    assert result["action_items"] == []
    assert result["classification"] == "spam"


def test_multiple_action_items():
    items = ["Schedule call", "Review proposal", "Send budget"]
    result = _call({"classification": "action-required", "confidence": 0.85, "action_items": items})
    assert result["action_items"] == items


@pytest.mark.parametrize("label", list(VALID_CLASSIFICATIONS))
def test_all_classification_labels_accepted(label):
    result = _call({"classification": label, "confidence": 0.9, "action_items": []})
    assert result["classification"] == label
