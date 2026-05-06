"""
Response Suggester Agent
Takes a classified email and generates 2-3 draft reply options.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an email response assistant. Given an email and its classification, suggest appropriate replies.

Approach by classification:
- URGENT: Acknowledge immediately, confirm you are taking action, offer specific help
- ACTION-REQUIRED: Confirm receipt and commit to each action item with a realistic timeline
- ROUTINE: Either a brief acknowledgment or explain why no reply is needed
- SPAM: Do not draft a reply. Provide one suggestion on how to handle it (mark as spam, delete, report)

For URGENT, ACTION-REQUIRED, and ROUTINE: generate 2-3 options with different tones (e.g. Formal, Casual, Brief).
Each option needs a label, a subject line using "Re: <original subject>", and a complete ready-to-send body.

Also suggest an improved subject line for the original email if the current one is vague, missing context,
or not searchable (e.g. "follow up" → "Q3 Budget Review: Feedback Needed by Friday"). If the original
subject is already clear and specific, return it unchanged."""

# Same pattern as the classifier — enforce a consistent JSON structure
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "suggested_subject": {"type": "string"},
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label":   {"type": "string"},
                    "subject": {"type": "string"},
                    "body":    {"type": "string"}
                },
                "required": ["label", "subject", "body"],
                "additionalProperties": False
            }
        }
    },
    "required": ["suggested_subject", "suggestions"],
    "additionalProperties": False
}


def suggest_responses(email: dict, classification: dict) -> dict:
    """
    Generate reply options for a classified email.

    Args:
        email:          dict with 'sender', 'subject', 'body'
        classification: dict with 'classification', 'confidence', 'action_items'

    Returns:
        dict with 'suggestions' — a list of {label, subject, body}
    """
    # Pass both the email content and what the classifier found
    action_text = ""
    if classification["action_items"]:
        lines = "\n".join(f"  - {item}" for item in classification["action_items"])
        action_text = f"\n\nIdentified action items:\n{lines}"

    prompt = (
        f"From: {email['sender']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}\n\n"
        f"Classification: {classification['classification'].upper()}"
        f"{action_text}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        # Cache the system prompt — it's the same for every email
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": RESPONSE_SCHEMA
            }
        },
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)


def print_suggestions(result: dict) -> None:
    """Print the response suggestions below a classified email."""
    suggested = result.get("suggested_subject", "")
    if suggested:
        print(f"\n  Suggested subject: {suggested}")

    print("\nSuggested Responses:")
    for i, s in enumerate(result["suggestions"], 1):
        print(f"\n  Option {i} [{s['label']}]")
        print(f"  Subject: {s['subject']}")
        print(f"  {'·' * 54}")
        for line in s["body"].strip().split("\n"):
            print(f"  {line}")
