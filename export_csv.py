"""
CSV Exporter
Writes the full pipeline results to a timestamped CSV file.
"""

import csv
import datetime
import os


def export_csv(rows: list, draft_choices: list, suggested_subjects: list = None, output_dir: str = None) -> str:
    """
    Write pipeline results to a CSV file.

    Args:
        rows:               list of (email, classification, priority) tuples, priority-sorted
        draft_choices:      list of draft labels saved per email (str or None), same order as rows
        suggested_subjects: list of improved subject lines per email (str or None), same order as rows
        output_dir:         directory to write the file (defaults to the script directory)

    Returns:
        absolute path of the written CSV file
    """
    if suggested_subjects is None:
        suggested_subjects = [None] * len(rows)
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"email_digest_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    fieldnames = [
        "rank",
        "date",
        "sender",
        "subject",
        "suggested_subject",
        "classification",
        "confidence",
        "priority_score",
        "priority_explanation",
        "action_items",
        "draft_saved",
        "exported_at",
    ]

    exported_at = datetime.datetime.now().isoformat(timespec="seconds")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rank, ((email, classification, priority), draft_label, suggested_subject) in enumerate(
            zip(rows, draft_choices, suggested_subjects), 1
        ):
            writer.writerow({
                "rank":                 rank,
                "date":                 email.get("date", ""),
                "sender":               email["sender"],
                "subject":              email["subject"],
                "suggested_subject":    suggested_subject or "",
                "classification":       classification["classification"].upper(),
                "confidence":           classification["confidence"],
                "priority_score":       priority["score"],
                "priority_explanation": priority["explanation"],
                "action_items":         "; ".join(classification["action_items"]),
                "draft_saved":          draft_label or "none",
                "exported_at":          exported_at,
            })

    return filepath
