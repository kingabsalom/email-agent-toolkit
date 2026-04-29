# Email Agent Toolkit

A multi-agent email processing pipeline powered by Claude AI. Three specialized agents work together to classify, prioritize, and draft responses for your inbox — output sorted by priority so you always know what to handle first.

## How It Works

Each agent is a focused Claude API call with a structured output schema:

```
Email Input
    │
    ├── classify_emails.py   → label + action items
    ├── score_priority.py    → priority score 1–10 + explanation
    └── suggest_responses.py → 2–3 draft reply options
            │
            ▼
        main.py  (runs all three, sorted by priority)
```

## Agents

| Agent | File | Output |
|---|---|---|
| Classifier | `classify_emails.py` | `urgent` / `action-required` / `routine` / `spam` + action items |
| Priority Scorer | `score_priority.py` | Score 1–10 + one-line explanation |
| Response Suggester | `suggest_responses.py` | 2–3 ready-to-send draft replies |

## Setup

**1. Clone and install dependencies**
```bash
git clone https://github.com/YOUR_USERNAME/email-agent-toolkit.git
cd email-agent-toolkit
pip3 install -r requirements.txt
```

**2. Set your Anthropic API key**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add it to your shell config so it persists:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

## Usage

**Run the full pipeline** (classify + score + respond, sorted by priority):
```bash
python3 main.py
```

**Run just the classifier:**
```bash
python3 classify_emails.py
```

**Use an agent in your own code:**
```python
from classify_emails import classify_email
from score_priority import score_priority
from suggest_responses import suggest_responses

email = {
    "sender": "manager@company.com",
    "subject": "Report due Friday",
    "body": "Please send your summary to Sarah by Thursday noon..."
}

classification = classify_email(email)
priority = score_priority(email, classification)
suggestions = suggest_responses(email, classification)
```

## Example Output

```
Processing 5 emails...
Classifying and scoring ..... done.

PRIORITY SUMMARY
──────────────────────────────────────────────────────────────────────────────
 #  Score  Classification    Items  Sender                  Subject
──────────────────────────────────────────────────────────────────────────────
 1  10/10  URGENT                3  it-alerts@company.com   CRITICAL: Production…
 2   9/10  ACTION-REQUIRED       4  manager@company.com     Q3 report due this Fr…
 3   8/10  ACTION-REQUIRED       3  alex@bigclient.com      Project proposal — fe…
 4   2/10  ROUTINE               0  newsletter@devweekly.io Dev Weekly #142: Rust…
 5   1/10  SPAM                  0  noreply@deals-unlimit…  You have been SELECTE…
──────────────────────────────────────────────────────────────────────────────

DETAILED VIEW  (sorted by priority)

────────────────────────────────────────────────────────────
Sender:         it-alerts@company.com
Subject:        CRITICAL: Production database down — immediate action needed
Classification: URGENT  (confidence: 99%)
Action Items:
  - Join the incident call immediately at https://meet.company.com/incident-001
  - Get all senior engineers on the call
  - Assign someone to update the status page every 10 minutes

Priority: 10/10 — URGENT with immediate deadline and 3 action items.

Suggested Responses:

  Option 1 [Formal]
  Subject: Re: CRITICAL: Production database down — immediate action needed
  ······················································
  Acknowledged. Joining the incident call now...
```

## Project Structure

```
email-agent-toolkit/
├── main.py                  # Full pipeline — runs all three agents
├── classify_emails.py       # Agent 1: classifier
├── score_priority.py        # Agent 2: priority scorer
├── suggest_responses.py     # Agent 3: response suggester
├── sample_emails.json       # Test data (5 sample emails)
├── requirements.txt
└── README.md
```

## Roadmap

- [ ] **Gmail integration** — connect to a real inbox via the Gmail API
- [ ] **CSV export** — write results to a spreadsheet for review
- [ ] **Sender reputation** — learn which senders are high-priority over time
- [ ] **Batch mode** — process a full inbox folder, not just a single JSON file
- [ ] **Web UI** — simple dashboard to view and act on prioritized emails
- [ ] **Auto-draft** — push top-ranked response drafts back to Gmail as drafts

## Notes

- All three agents use `claude-opus-4-7` with structured JSON output schemas, so responses are always parseable.
- The system prompt for each agent is cached across requests — after the first email, subsequent calls are faster and cheaper.
- Each agent file is independently importable and works as a standalone script.
