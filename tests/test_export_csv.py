import csv
import os
import tempfile
import pytest
from tests.conftest import SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE


def _make_rows(n=3):
    return [(SAMPLE_EMAIL, CLASSIFY_RESPONSE, SCORE_RESPONSE)] * n


def test_creates_file():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(1), [None], output_dir=tmpdir)
        assert os.path.isfile(path)


def test_filename_contains_timestamp():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(1), [None], output_dir=tmpdir)
        assert "email_digest_" in os.path.basename(path)
        assert path.endswith(".csv")


def test_correct_headers():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(1), [None], output_dir=tmpdir)
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == {
                "rank", "date", "sender", "subject", "suggested_subject",
                "classification", "confidence", "priority_score",
                "priority_explanation", "action_items", "draft_saved", "exported_at",
            }


def test_row_count_matches_input():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(4), [None] * 4, output_dir=tmpdir)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 4


def test_draft_saved_column_shows_label():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(2), ["Formal", None], output_dir=tmpdir)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["draft_saved"] == "Formal"
        assert rows[1]["draft_saved"] == "none"


def test_rank_increments():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(3), [None] * 3, output_dir=tmpdir)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert [r["rank"] for r in rows] == ["1", "2", "3"]


def test_action_items_joined_by_semicolon():
    from export_csv import export_csv
    classification = {**CLASSIFY_RESPONSE, "action_items": ["Task A", "Task B"]}
    rows = [(SAMPLE_EMAIL, classification, SCORE_RESPONSE)]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(rows, [None], output_dir=tmpdir)
        with open(path, newline="") as f:
            row = list(csv.DictReader(f))[0]
        assert row["action_items"] == "Task A; Task B"


def test_suggested_subject_written_to_csv():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(1), [None], ["Improved Subject Line"], output_dir=tmpdir)
        with open(path, newline="") as f:
            row = list(csv.DictReader(f))[0]
        assert row["suggested_subject"] == "Improved Subject Line"


def test_suggested_subject_empty_when_not_provided():
    from export_csv import export_csv
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(_make_rows(1), [None], output_dir=tmpdir)
        with open(path, newline="") as f:
            row = list(csv.DictReader(f))[0]
        assert row["suggested_subject"] == ""
