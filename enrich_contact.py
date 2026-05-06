"""
Contact Enricher
Uses Claude to infer company, role, and domain type from a sender's email address.
Results are cached locally so each contact is only looked up once.
"""

import json
import os
import re
import anthropic

client = anthropic.Anthropic()

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts_cache.json")

SYSTEM_PROMPT = """You are a contact intelligence assistant. Given a sender's display name and email
address, infer as much as you can about them from available signals.

Use the domain, name patterns, and common conventions to determine:
- name: their cleaned-up display name (remove angle brackets, extra formatting)
- company: their organization inferred from the domain (e.g. bigclient.com → BigClient, google.com → Google)
- domain_type: one of "personal" (gmail/yahoo/hotmail/outlook/icloud),
  "corporate", "nonprofit", "government" (.gov/.edu), or "automated" (noreply/alerts/notifications/no-reply)
- title: their likely job title or role if inferrable from email patterns or name (empty string if unknown)

Be concise and factual. Use empty string when you cannot determine a value."""

ENRICH_SCHEMA = {
    "type": "object",
    "properties": {
        "name":        {"type": "string"},
        "company":     {"type": "string"},
        "domain_type": {
            "type": "string",
            "enum": ["personal", "corporate", "nonprofit", "government", "automated"]
        },
        "title":       {"type": "string"},
    },
    "required": ["name", "company", "domain_type", "title"],
    "additionalProperties": False,
}


def _extract_email_address(sender: str) -> str:
    """Extract bare email address from 'Display Name <email@domain>' format."""
    match = re.search(r"<([^>]+)>", sender)
    return match.group(1).strip().lower() if match else sender.strip().lower()


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                content = f.read().strip()
            return json.loads(content) if content else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def enrich_contact(sender: str) -> dict:
    """
    Enrich a sender string with inferred contact information.

    Args:
        sender: raw From header value, e.g. "Alex Smith <alex@bigclient.com>"

    Returns:
        dict with name, company, domain_type, title
    """
    email_addr = _extract_email_address(sender)
    cache = _load_cache()

    if email_addr in cache:
        return cache[email_addr]

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        output_config={"format": {"type": "json_schema", "schema": ENRICH_SCHEMA}},
        messages=[{"role": "user", "content": f"Sender: {sender}"}]
    )

    result = json.loads(response.content[0].text)
    cache[email_addr] = result
    _save_cache(cache)
    return result
