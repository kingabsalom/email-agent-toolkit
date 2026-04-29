"""
Priority Scorer Agent
Scores each email 1-10 based on urgency, deadlines, action items, and sender importance.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an email priority scoring assistant. Score each email from 1 to 10.

Use these factors to determine the score:

1. Classification (base score):
   - URGENT: 8-10
   - ACTION-REQUIRED: 5-7
   - ROUTINE: 2-4
   - SPAM: 1

2. Adjust up or down based on:
   - Deadline urgency: "immediately" or "now" = +2, "this week" = +1, no deadline = 0
   - Action item count: 3 or more items = +1
   - Sender importance: manager, client, executive, or C-suite = +1; automated sender = -1

Return a score (integer 1-10) and one concise sentence explaining the main factors."""

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer"
        },
        "explanation": {
            "type": "string"
        }
    },
    "required": ["score", "explanation"],
    "additionalProperties": False
}


def score_priority(email: dict, classification: dict) -> dict:
    """
    Score the priority of a classified email.

    Args:
        email:          dict with 'sender', 'subject', 'body'
        classification: dict with 'classification', 'confidence', 'action_items'

    Returns:
        dict with 'score' (int 1-10) and 'explanation' (str)
    """
    action_text = ""
    if classification["action_items"]:
        lines = "\n".join(f"  - {item}" for item in classification["action_items"])
        action_text = f"\n\nAction items:\n{lines}"

    prompt = (
        f"From: {email['sender']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}\n\n"
        f"Classification: {classification['classification'].upper()}"
        f"{action_text}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": SCORE_SCHEMA
            }
        },
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)
