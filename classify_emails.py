"""
Email Classification System
Reads emails from sample_emails.json and uses Claude to classify each one.
"""

import json
import os
import anthropic

# The client automatically reads ANTHROPIC_API_KEY from your environment.
client = anthropic.Anthropic()

# We define the instructions once and reuse them for every email.
SYSTEM_PROMPT = """You are an email classification assistant. For each email:

1. Classify it as exactly one of these categories:
   - urgent: Needs immediate attention (outages, emergencies, critical deadlines)
   - action-required: Contains tasks, requests, or questions that need a response
   - routine: Informational only — newsletters, FYIs, no action needed
   - spam: Unsolicited promotions, phishing attempts, or suspicious content

2. Extract any specific action items (concrete tasks, deadlines, or requests)

3. Rate your confidence from 0.0 (uncertain) to 1.0 (very confident)"""

# This schema tells Claude exactly what JSON structure to return.
# Enforcing a schema means we always get valid, parseable output.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["urgent", "routine", "spam", "action-required"]
        },
        "confidence": {
            "type": "number"
        },
        "action_items": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["classification", "confidence", "action_items"],
    "additionalProperties": False
}


def classify_email(email: dict) -> dict:
    """
    Send one email to Claude and return its classification.

    Args:
        email: dict with keys 'sender', 'subject', 'body'

    Returns:
        dict with keys 'classification', 'confidence', 'action_items'
    """
    # Format the email content the same way a human would read it
    email_text = (
        f"From: {email['sender']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        # Pass system as a list so we can add cache_control.
        # Caching means Claude only processes the system prompt once —
        # every request after the first reuses the cached version (faster + cheaper).
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        # output_config forces Claude to respond with JSON that matches our schema
        output_config={
            "format": {
                "type": "json_schema",
                "schema": RESPONSE_SCHEMA
            }
        },
        messages=[{"role": "user", "content": email_text}]
    )

    # When output_config is used, the response is guaranteed to be valid JSON
    return json.loads(response.content[0].text)


def print_summary(email: dict, result: dict) -> None:
    """Print a human-readable summary for one classified email."""
    label = result["classification"].upper()
    confidence = f"{int(result['confidence'] * 100)}%"

    print(f"\n{'─' * 60}")
    print(f"Sender:         {email['sender']}")
    print(f"Subject:        {email['subject']}")
    print(f"Classification: {label}  (confidence: {confidence})")

    if result["action_items"]:
        print("Action Items:")
        for item in result["action_items"]:
            print(f"  - {item}")
    else:
        print("Action Items:   None")


def main():
    # Find sample_emails.json in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    emails_path = os.path.join(script_dir, "sample_emails.json")

    with open(emails_path) as f:
        emails = json.load(f)

    print(f"Classifying {len(emails)} emails...\n")

    for email in emails:
        result = classify_email(email)
        print_summary(email, result)

    print(f"\n{'─' * 60}")
    print("Done.")


if __name__ == "__main__":
    main()
