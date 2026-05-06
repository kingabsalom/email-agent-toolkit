import datetime
from unittest.mock import MagicMock, patch
from tests.conftest import SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE


def _make_rows(n=3):
    return [(SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE)] * n


def _make_mixed_rows():
    """Rows with varied classifications for count testing."""
    urgent = (SAMPLE_EMAIL, {**CLASSIFY_RESPONSE, "classification": "urgent"}, SCORE_RESPONSE)
    action = (SAMPLE_EMAIL, {**CLASSIFY_RESPONSE, "classification": "action-required"}, SCORE_RESPONSE)
    routine = (SAMPLE_EMAIL, {**CLASSIFY_RESPONSE, "classification": "routine"}, SCORE_RESPONSE)
    spam = (SAMPLE_EMAIL, {**CLASSIFY_RESPONSE, "classification": "spam"}, SCORE_RESPONSE)
    return [urgent, action, routine, spam]


# --- format_digest tests (pure function, no mocking needed) ---

def test_format_digest_contains_date():
    from digest_email import format_digest
    result = format_digest(_make_rows(1))
    today = datetime.date.today().strftime("%Y")
    assert today in result


def test_format_digest_contains_email_count():
    from digest_email import format_digest
    result = format_digest(_make_rows(3))
    assert "3 emails" in result


def test_format_digest_counts_by_classification():
    from digest_email import format_digest
    result = format_digest(_make_mixed_rows())
    assert "1 urgent" in result
    assert "1 action-required" in result
    assert "1 routine" in result
    assert "1 spam" in result


def test_format_digest_includes_sender():
    from digest_email import format_digest
    result = format_digest(_make_rows(1))
    assert SAMPLE_EMAIL["sender"] in result


def test_format_digest_shows_suggested_subject_when_different():
    from digest_email import format_digest
    suggested = ["A Much Better Subject Line"]
    result = format_digest(_make_rows(1), suggested_subjects=suggested)
    assert "A Much Better Subject Line" in result


def test_format_digest_omits_suggested_subject_when_same():
    from digest_email import format_digest
    same_subject = [SAMPLE_EMAIL["subject"]]
    result = format_digest(_make_rows(1), suggested_subjects=same_subject)
    assert result.count(SAMPLE_EMAIL["subject"]) == 2  # once in table, once in detail — not three


def test_format_digest_shows_action_items():
    from digest_email import format_digest
    result = format_digest(_make_rows(1))
    for item in CLASSIFY_RESPONSE["action_items"]:
        assert item in result


def test_format_digest_shows_priority_score():
    from digest_email import format_digest
    result = format_digest(_make_rows(1))
    assert f"{SCORE_RESPONSE['score']}/10" in result


def test_format_digest_includes_followup_reminders():
    from digest_email import format_digest
    reminders = [{"subject": "Project update", "to": "boss@co.com", "sent_date": "2026-05-01", "days_waiting": 5}]
    result = format_digest(_make_rows(1), reminders=reminders)
    assert "FOLLOW-UP REMINDERS" in result
    assert "Project update" in result
    assert "5d waiting" in result


def test_format_digest_no_reminders_section_when_empty():
    from digest_email import format_digest
    result = format_digest(_make_rows(1), reminders=[])
    assert "FOLLOW-UP REMINDERS" not in result


# --- send_digest tests (mock Gmail API) ---

def _mock_service(user_email="me@example.com"):
    mock = MagicMock()
    mock.users.return_value.getProfile.return_value.execute.return_value = {"emailAddress": user_email}
    mock.users.return_value.messages.return_value.send.return_value.execute.return_value = {"id": "msg_123"}
    return mock


def test_send_digest_returns_recipient_email():
    from digest_email import send_digest
    with patch("digest_email.get_service", return_value=_mock_service("user@gmail.com")):
        result = send_digest(_make_rows(1))
    assert result == "user@gmail.com"


def test_send_digest_calls_messages_send():
    from digest_email import send_digest
    mock_service = _mock_service()
    with patch("digest_email.get_service", return_value=mock_service):
        send_digest(_make_rows(1))
    assert mock_service.users.return_value.messages.return_value.send.called


def test_send_digest_subject_contains_date_and_count():
    import base64, email as email_lib
    from email.header import decode_header
    from digest_email import send_digest
    mock_service = _mock_service()
    with patch("digest_email.get_service", return_value=mock_service):
        send_digest(_make_rows(2))

    call_kwargs = mock_service.users.return_value.messages.return_value.send.call_args.kwargs
    raw = base64.urlsafe_b64decode(call_kwargs["body"]["raw"]).decode()
    msg = email_lib.message_from_string(raw)
    # Decode the potentially UTF-8-encoded subject header
    decoded_parts = decode_header(msg["Subject"])
    subject = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )
    assert "2 emails" in subject
    assert str(datetime.date.today().year) in subject


def test_send_digest_subject_includes_followup_count():
    import base64, email as email_lib
    from email.header import decode_header
    from digest_email import send_digest
    mock_service = _mock_service()
    reminders = [{"subject": "Hi", "to": "x@y.com", "sent_date": "2026-05-01", "days_waiting": 4}]
    with patch("digest_email.get_service", return_value=mock_service):
        send_digest(_make_rows(1), reminders=reminders)
    call_kwargs = mock_service.users.return_value.messages.return_value.send.call_args.kwargs
    raw = base64.urlsafe_b64decode(call_kwargs["body"]["raw"]).decode()
    msg = email_lib.message_from_string(raw)
    decoded_parts = decode_header(msg["Subject"])
    subject = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )
    assert "follow-up" in subject.lower()
