import json
import os
import tempfile
from unittest.mock import patch
from tests.conftest import SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE


def _tmp():
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    return f.name


# --- record_interaction ---

def test_record_creates_entry():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction
            record_interaction("alex@bigclient.com")
        with open(path) as f:
            db = json.load(f)
        assert "alex@bigclient.com" in db
        assert db["alex@bigclient.com"]["total_received"] == 1
    finally:
        os.unlink(path)


def test_record_increments_on_repeat():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction
            record_interaction("alex@bigclient.com")
            record_interaction("alex@bigclient.com")
        with open(path) as f:
            db = json.load(f)
        assert db["alex@bigclient.com"]["total_received"] == 2
    finally:
        os.unlink(path)


def test_record_marks_responded():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction
            record_interaction("alex@bigclient.com", responded=True)
        with open(path) as f:
            db = json.load(f)
        assert db["alex@bigclient.com"]["total_responded"] == 1
    finally:
        os.unlink(path)


def test_record_extracts_email_from_display_name():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction
            record_interaction("Alex Smith <ALEX@BigClient.COM>")
        with open(path) as f:
            db = json.load(f)
        assert "alex@bigclient.com" in db
    finally:
        os.unlink(path)


# --- get_reputation ---

def test_get_reputation_unknown_sender():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import get_reputation
            result = get_reputation("unknown@example.com")
        assert result["total_received"] == 0
        assert result["response_rate"] is None
        assert result["is_frequent"] is False
        assert result["is_responsive"] is False
    finally:
        os.unlink(path)


def test_get_reputation_computes_response_rate():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction, get_reputation
            for _ in range(4):
                record_interaction("alex@bigclient.com")
            for _ in range(2):
                record_interaction("alex@bigclient.com", responded=True)
            result = get_reputation("alex@bigclient.com")
        assert result["total_received"] == 6
        assert result["response_rate"] == round(2 / 6, 2)
    finally:
        os.unlink(path)


def test_is_frequent_after_five_emails():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction, get_reputation
            for _ in range(5):
                record_interaction("boss@company.com")
            result = get_reputation("boss@company.com")
        assert result["is_frequent"] is True
    finally:
        os.unlink(path)


def test_is_responsive_above_fifty_percent():
    path = _tmp()
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import record_interaction, get_reputation
            record_interaction("boss@company.com", responded=True)
            record_interaction("boss@company.com", responded=True)
            record_interaction("boss@company.com", responded=False)
            result = get_reputation("boss@company.com")
        assert result["is_responsive"] is True
    finally:
        os.unlink(path)


# --- update_from_session ---

def test_update_from_session_records_all_emails():
    path = _tmp()
    rows = [(SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE)] * 3
    try:
        with patch("reputation.REPUTATION_FILE", path):
            from reputation import update_from_session, get_reputation
            update_from_session(rows, [None, "Formal", None])
            result = get_reputation(SAMPLE_EMAIL["sender"])
        assert result["total_received"] == 3
        # 1 response out of 3 received
        assert result["response_rate"] == round(1 / 3, 2)
    finally:
        os.unlink(path)


# --- score_priority integration ---

def test_score_priority_accepts_reputation():
    from unittest.mock import patch as p
    from tests.conftest import mock_api_response, CLASSIFY_RESPONSE, SAMPLE_EMAIL
    reputation = {"response_rate": 0.8, "total_received": 10, "is_frequent": True, "is_responsive": True}
    payload = {"score": 8, "explanation": "Responsive sender, urgent content."}
    with p("score_priority.client.messages.create", return_value=mock_api_response(payload)) as mock_api:
        from score_priority import score_priority
        result = score_priority(SAMPLE_EMAIL, CLASSIFY_RESPONSE, reputation=reputation)
    assert result["score"] == 8
    call_prompt = mock_api.call_args.kwargs["messages"][0]["content"]
    assert "80%" in call_prompt
