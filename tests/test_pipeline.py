"""
Integration test: runs the full classify → score → suggest pipeline
against sample_emails.json with mocked Claude API calls, then verifies
the CSV export contains the expected output.
"""

import csv
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from tests.conftest import CLASSIFY_RESPONSE, SCORE_RESPONSE, SUGGEST_RESPONSE, mock_api_response

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_emails.json")
VALID_CLASSIFICATIONS = {"urgent", "action-required", "routine", "spam"}


def load_sample_emails():
    with open(SAMPLE_PATH) as f:
        return json.load(f)


def run_pipeline(emails):
    """Run classify + score + suggest for each email with mocked API calls."""
    from classify_emails import classify_email
    from score_priority import score_priority
    from suggest_responses import suggest_responses

    rows = []
    draft_choices = []

    with patch("classify_emails.client.messages.create", return_value=mock_api_response(CLASSIFY_RESPONSE)), \
         patch("score_priority.client.messages.create", return_value=mock_api_response(SCORE_RESPONSE)), \
         patch("suggest_responses.client.messages.create", return_value=mock_api_response(SUGGEST_RESPONSE)):

        for email in emails:
            classification = classify_email(email)
            priority = score_priority(email, classification)
            suggestions = suggest_responses(email, classification)
            rows.append((email, classification, priority))
            draft_choices.append(None)

    return rows, draft_choices


def test_pipeline_processes_all_sample_emails():
    emails = load_sample_emails()
    rows, _ = run_pipeline(emails)
    assert len(rows) == len(emails)


def test_pipeline_classifications_are_valid():
    emails = load_sample_emails()
    rows, _ = run_pipeline(emails)
    for _, classification, _ in rows:
        assert classification["classification"] in VALID_CLASSIFICATIONS


def test_pipeline_scores_are_in_range():
    emails = load_sample_emails()
    rows, _ = run_pipeline(emails)
    for _, _, priority in rows:
        assert 1 <= priority["score"] <= 10


def test_pipeline_exports_correct_row_count():
    from export_csv import export_csv
    emails = load_sample_emails()
    rows, draft_choices = run_pipeline(emails)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(rows, draft_choices, output_dir=tmpdir)
        with open(path, newline="") as f:
            csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == len(emails)


def test_pipeline_csv_has_valid_senders():
    from export_csv import export_csv
    emails = load_sample_emails()
    rows, draft_choices = run_pipeline(emails)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_csv(rows, draft_choices, output_dir=tmpdir)
        with open(path, newline="") as f:
            csv_rows = list(csv.DictReader(f))
    senders_in_csv = {r["sender"] for r in csv_rows}
    senders_in_emails = {e["sender"] for e in emails}
    assert senders_in_csv == senders_in_emails
