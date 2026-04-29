"""
Email Pipeline
Classifies, scores, and suggests responses — sorted by priority.

Usage:
    python3 main.py
"""

import json
import os
from classify_emails import classify_email, print_summary
from suggest_responses import suggest_responses, print_suggestions
from score_priority import score_priority


def truncate(text: str, max_len: int) -> str:
    """Shorten a string to max_len, adding '…' if cut."""
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def print_summary_table(rows: list) -> None:
    """Print a compact priority-sorted summary table."""
    # Fixed column widths
    W = {"rank": 2, "score": 5, "label": 16, "items": 5, "sender": 26, "subject": 32}
    rule_width = sum(W.values()) + len(W) * 2  # add 2 spaces between each column

    header = (
        f"{'#':>{W['rank']}}  "
        f"{'Score':>{W['score']}}  "
        f"{'Classification':<{W['label']}}  "
        f"{'Items':>{W['items']}}  "
        f"{'Sender':<{W['sender']}}  "
        f"Subject"
    )

    print("\nPRIORITY SUMMARY")
    print("─" * rule_width)
    print(header)
    print("─" * rule_width)

    for rank, (email, classification, priority) in enumerate(rows, 1):
        label = classification["classification"].upper()
        n_items = len(classification["action_items"])
        print(
            f"{rank:>{W['rank']}}  "
            f"{priority['score']:>2}/10  "
            f"{label:<{W['label']}}  "
            f"{n_items:>{W['items']}}  "
            f"{truncate(email['sender'], W['sender']):<{W['sender']}}  "
            f"{truncate(email['subject'], W['subject'])}"
        )

    print("─" * rule_width)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "sample_emails.json")) as f:
        emails = json.load(f)

    print(f"Processing {len(emails)} emails...")

    # Phase 1: classify and score every email (dots show progress)
    print("Classifying and scoring ", end="", flush=True)
    rows = []
    for email in emails:
        classification = classify_email(email)
        priority = score_priority(email, classification)
        rows.append((email, classification, priority))
        print(".", end="", flush=True)
    print(" done.\n")

    # Phase 2: sort highest priority first
    rows.sort(key=lambda row: row[2]["score"], reverse=True)

    # Phase 3: summary table
    print_summary_table(rows)

    # Phase 4: full details + response suggestions in priority order
    print("\n\nDETAILED VIEW  (sorted by priority)\n")
    for rank, (email, classification, priority) in enumerate(rows, 1):
        print_summary(email, classification)
        print(f"\nPriority: {priority['score']}/10 — {priority['explanation']}")
        suggestions = suggest_responses(email, classification)
        print_suggestions(suggestions)

    print(f"\n{'─' * 60}")
    print("Done.")


if __name__ == "__main__":
    main()
