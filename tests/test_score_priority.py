import pytest
from unittest.mock import patch
from tests.conftest import SAMPLE_EMAIL, CLASSIFY_RESPONSE, mock_api_response


def _call(score, explanation="Looks important."):
    from score_priority import score_priority
    payload = {"score": score, "explanation": explanation}
    with patch("score_priority.client.messages.create", return_value=mock_api_response(payload)):
        return score_priority(SAMPLE_EMAIL, CLASSIFY_RESPONSE)


def test_score_is_integer():
    result = _call(8)
    assert isinstance(result["score"], int)


def test_score_within_range():
    result = _call(7)
    assert 1 <= result["score"] <= 10


def test_explanation_is_nonempty_string():
    result = _call(5, "Moderate priority.")
    assert isinstance(result["explanation"], str)
    assert len(result["explanation"]) > 0


@pytest.mark.parametrize("score", [1, 5, 10])
def test_boundary_scores_accepted(score):
    result = _call(score)
    assert result["score"] == score


def test_works_with_no_action_items():
    from score_priority import score_priority
    classification = {"classification": "routine", "confidence": 0.6, "action_items": []}
    payload = {"score": 3, "explanation": "Routine newsletter."}
    with patch("score_priority.client.messages.create", return_value=mock_api_response(payload)):
        result = score_priority(SAMPLE_EMAIL, classification)
    assert result["score"] == 3


def test_accepts_contact_enrichment():
    from score_priority import score_priority
    contact = {"name": "Alex Smith", "company": "BigClient", "domain_type": "corporate", "title": "VP Sales"}
    payload = {"score": 8, "explanation": "Senior contact at a corporate client."}
    with patch("score_priority.client.messages.create", return_value=mock_api_response(payload)) as mock_api:
        result = score_priority(SAMPLE_EMAIL, CLASSIFY_RESPONSE, contact=contact)
    assert result["score"] == 8
    call_prompt = mock_api.call_args.kwargs["messages"][0]["content"]
    assert "BigClient" in call_prompt


def test_contact_none_does_not_break():
    result = _call(7)
    assert result["score"] == 7
