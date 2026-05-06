import base64
import email as email_lib
from unittest.mock import MagicMock, patch


def _make_mock_service(draft_id="draft_abc", message_id="msg_xyz"):
    mock_service = MagicMock()
    mock_service.users.return_value \
        .drafts.return_value \
        .create.return_value \
        .execute.return_value = {
            "id": draft_id,
            "message": {"id": message_id},
        }
    return mock_service


def test_returns_draft_id_and_message_id():
    from create_draft import create_draft
    with patch("create_draft.get_service", return_value=_make_mock_service()):
        result = create_draft("to@example.com", "Re: Hello", "Hi there.")
    assert result["id"] == "draft_abc"
    assert result["message_id"] == "msg_xyz"


def test_calls_drafts_create_with_raw_message():
    from create_draft import create_draft
    mock_service = _make_mock_service()
    with patch("create_draft.get_service", return_value=mock_service):
        create_draft("to@example.com", "Re: Hello", "Body text.")

    call_kwargs = mock_service.users.return_value.drafts.return_value.create.call_args.kwargs
    assert call_kwargs["userId"] == "me"
    raw = call_kwargs["body"]["message"]["raw"]
    decoded = base64.urlsafe_b64decode(raw).decode()
    assert "Body text." in decoded


def test_mime_headers_set_correctly():
    from create_draft import create_draft
    mock_service = _make_mock_service()
    with patch("create_draft.get_service", return_value=mock_service):
        create_draft("recipient@example.com", "Re: Test Subject", "Hello!")

    call_kwargs = mock_service.users.return_value.drafts.return_value.create.call_args.kwargs
    raw = base64.urlsafe_b64decode(call_kwargs["body"]["message"]["raw"]).decode()
    msg = email_lib.message_from_string(raw)
    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Re: Test Subject"


def test_get_service_called_once():
    from create_draft import create_draft
    with patch("create_draft.get_service", return_value=_make_mock_service()) as mock_gs:
        create_draft("x@y.com", "Re: X", "Body.")
    mock_gs.assert_called_once()
