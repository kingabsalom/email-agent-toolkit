from unittest.mock import MagicMock, patch
from tests.conftest import SAMPLE_EMAIL


def _mock_tasks_service(task_ids=None):
    task_ids = task_ids or ["task_1", "task_2"]
    mock = MagicMock()
    side_effects = [
        {"id": tid, "title": f"Task {i+1}"} for i, tid in enumerate(task_ids)
    ]
    mock.tasks.return_value.insert.return_value.execute.side_effect = side_effects
    return mock


def test_creates_one_task_per_action_item():
    from create_tasks import create_tasks
    items = ["Reply to proposal", "Schedule call for Thursday"]
    mock_svc = _mock_tasks_service(["t1", "t2"])
    with patch("create_tasks.get_tasks_service", return_value=mock_svc):
        result = create_tasks(items, SAMPLE_EMAIL)
    assert len(result) == 2
    assert mock_svc.tasks.return_value.insert.call_count == 2


def test_returns_list_of_task_dicts():
    from create_tasks import create_tasks
    mock_svc = _mock_tasks_service(["t1"])
    with patch("create_tasks.get_tasks_service", return_value=mock_svc):
        result = create_tasks(["One task"], SAMPLE_EMAIL)
    assert isinstance(result, list)
    assert "id" in result[0]
    assert "title" in result[0]


def test_task_inserted_to_default_tasklist():
    from create_tasks import create_tasks
    mock_svc = _mock_tasks_service(["t1"])
    with patch("create_tasks.get_tasks_service", return_value=mock_svc):
        create_tasks(["Task A"], SAMPLE_EMAIL)
    call_kwargs = mock_svc.tasks.return_value.insert.call_args.kwargs
    assert call_kwargs["tasklist"] == "@default"


def test_task_notes_include_sender_and_subject():
    from create_tasks import create_tasks
    mock_svc = _mock_tasks_service(["t1"])
    with patch("create_tasks.get_tasks_service", return_value=mock_svc):
        create_tasks(["Task A"], SAMPLE_EMAIL)
    body = mock_svc.tasks.return_value.insert.call_args.kwargs["body"]
    assert SAMPLE_EMAIL["sender"] in body["notes"]
    assert SAMPLE_EMAIL["subject"] in body["notes"]


def test_empty_action_items_returns_empty_list():
    from create_tasks import create_tasks
    mock_svc = _mock_tasks_service([])
    with patch("create_tasks.get_tasks_service", return_value=mock_svc):
        result = create_tasks([], SAMPLE_EMAIL)
    assert result == []
