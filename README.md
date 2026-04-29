# Email Agent Toolkit

> Production-ready AI email pipeline that classifies, prioritizes, and drafts responses using a multi-agent Claude AI architecture with OAuth2 Gmail integration.

Built as both a working productivity tool and a demonstration of modern AI application patterns: multi-agent design, structured outputs, prompt caching, and secure OAuth2 credential management.

---

## What It Does

Drop this into your inbox and it will:

1. **Read** your last 10 Gmail emails (or run offline with sample data)
2. **Classify** each as `urgent`, `action-required`, `routine`, or `spam`
3. **Score** priority 1–10 using deadlines, sender importance, and action item density
4. **Draft** 2–3 ready-to-send response options per email
5. **Output** a ranked summary table followed by full details — highest priority first

```
PRIORITY SUMMARY
──────────────────────────────────────────────────────────────────────────────
 #  Score  Classification    Items  Sender                  Subject
──────────────────────────────────────────────────────────────────────────────
 1  10/10  URGENT                3  it-alerts@company.com   CRITICAL: Prod DB…
 2   9/10  ACTION-REQUIRED       4  manager@company.com     Q3 report due Fri…
 3   8/10  ACTION-REQUIRED       3  alex@bigclient.com      Project proposal…
 4   2/10  ROUTINE               0  newsletter@devweekly.io Dev Weekly #142…
 5   1/10  SPAM                  0  noreply@deals-unlimit…  You've been SELEC…
──────────────────────────────────────────────────────────────────────────────
```

---

## Key Features

- **Multi-agent architecture** — three independent Claude agents, each with a focused responsibility and structured JSON output schema
- **Real Gmail integration** — OAuth2 authentication, token persistence, multipart MIME body extraction
- **Structured outputs** — JSON schemas enforce consistent, parseable responses from every agent; no prompt hacking needed
- **Prompt caching** — system prompts are cached across requests using `cache_control`, reducing per-email API cost after the first call
- **Graceful fallback** — runs on sample data with no credentials required; switches to live Gmail automatically when `credentials.json` is present
- **Modular design** — each agent is independently importable and usable in other projects

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                      main.py                        │
│  load_emails() → classify → score → sort → suggest  │
└──────────┬──────────────────────────────────────────┘
           │
    ┌──────▼──────┐     ┌───────────────┐
    │ Gmail / JSON│     │  Claude API   │
    │  (input)    │     │  (3 agents)   │
    └──────┬──────┘     └───────┬───────┘
           │                    │
           ▼                    ▼
  gmail_reader.py     ┌─────────────────────┐
  OAuth2 + MIME  ───▶ │ classify_emails.py  │ → label + action items
  body extraction     │ score_priority.py   │ → score 1–10 + explanation
                      │ suggest_responses.py│ → 2–3 draft replies
                      └─────────────────────┘
```

### Agent Details

| Agent | Model | Max Tokens | Output Schema |
|---|---|---|---|
| Classifier | claude-opus-4-7 | 512 | `classification`, `confidence`, `action_items[]` |
| Priority Scorer | claude-opus-4-7 | 256 | `score`, `explanation` |
| Response Suggester | claude-opus-4-7 | 1024 | `suggestions[]{label, subject, body}` |

### Engineering Decisions

**Structured outputs over prompt engineering** — each agent uses `output_config` with a strict JSON schema. This eliminates parsing fragility and guarantees the downstream pipeline always receives valid data, even if Claude's phrasing changes between calls.

**Prompt caching** — the system prompt for each agent is identical across all emails in a run. Marking it with `cache_control: ephemeral` means Claude processes it once and serves subsequent requests from cache — typically 10× cheaper for cached tokens.

**Body truncation at 2,000 characters** — real emails can be arbitrarily long. Truncating before sending to Claude keeps token usage predictable without meaningfully affecting classification quality for triage purposes.

**Agents are stateless and composable** — each module exposes a plain Python function (`classify_email`, `score_priority`, `suggest_responses`). They share no state, can be tested in isolation, and can be imported into other projects without pulling in the full pipeline.

**Credential isolation** — `credentials.json` and `token.pickle` are excluded from version control via `.gitignore`. The OAuth token is stored in a binary pickle file rather than a plain-text config to reduce accidental exposure risk.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| AI | Anthropic Claude API (`claude-opus-4-7`) |
| AI SDK | `anthropic` (structured outputs, prompt caching) |
| Email | Google Gmail API v1 |
| Auth | OAuth2 via `google-auth-oauthlib` |
| HTTP | `google-auth-httplib2`, `google-api-python-client` |

---

## Project Evolution

### Phase 1 — MVP (classifier + scorer + response suggester)
Built three focused AI agents, each returning structured JSON. Validated the full pipeline on curated sample emails covering all four classification categories. Introduced prompt caching at this stage to control costs before connecting real data.

### Phase 2 — Production Gmail Integration
Added OAuth2 authentication with token persistence, multipart MIME parsing, and a fallback layer so the tool works with or without credentials. Real inbox emails are now the primary input.

### Phase 3 — Planned
- [ ] CSV / spreadsheet export of classified email log
- [ ] Scheduled runs (cron / launchd) with daily digest output
- [ ] Sender reputation model — learn which senders consistently score high
- [ ] Webhook mode — process incoming emails in real time
- [ ] Confidence threshold filtering — only show emails above a set score
- [ ] Web dashboard — browser UI for reviewing and acting on prioritized emails
- [ ] Auto-draft — push top-ranked response options back to Gmail as drafts

---

## Use Cases

**Consulting & professional services** — triage a high-volume client inbox, ensure urgent requests never get buried, and arrive at calls with drafted responses already prepared.

**Executive assistants** — run on a shared inbox to surface action items and draft replies for review before sending.

**Productivity automation** — connect to a work Gmail account and run as a morning digest before starting the day.

**Internal tooling** — extend the classifier to route emails to the right team member based on subject matter.

---

## Getting Started

### Quick Start (no Gmail credentials needed)

```bash
git clone https://github.com/kingabsalom/email-agent-toolkit.git
cd email-agent-toolkit
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python3 main.py
```

Runs against the included `sample_emails.json` with five realistic test cases.

### Production Setup (live Gmail inbox)

**1. Enable the Gmail API**
- Go to [console.cloud.google.com](https://console.cloud.google.com) → New project
- **APIs & Services → Library** → search "Gmail API" → Enable
- **APIs & Services → Credentials → Create Credentials → OAuth client ID**
  - Application type: **Desktop app**
  - Download JSON → rename to `credentials.json`

**2. Install and configure**

```bash
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

**3. Place credentials and run**

```bash
cp ~/Downloads/credentials.json ./credentials.json
python3 main.py
```

A browser window opens on first run — sign in and click **Allow**. A `token.pickle` is saved automatically; subsequent runs skip the browser step.

### Using Individual Agents

```python
from classify_emails import classify_email
from score_priority import score_priority
from suggest_responses import suggest_responses

email = {
    "sender": "manager@company.com",
    "subject": "Report due Friday",
    "body": "Please send your summary to Sarah by Thursday noon..."
}

classification = classify_email(email)   # → {classification, confidence, action_items}
priority       = score_priority(email, classification)   # → {score, explanation}
suggestions    = suggest_responses(email, classification) # → {suggestions[]}
```

---

## Project Structure

```
email-agent-toolkit/
├── main.py                  # Pipeline orchestrator — classify, score, sort, suggest
├── gmail_reader.py          # Gmail OAuth2 client + MIME body extractor
├── classify_emails.py       # Agent 1: email classifier
├── score_priority.py        # Agent 2: priority scorer
├── suggest_responses.py     # Agent 3: response drafter
├── sample_emails.json       # Offline test data (5 emails, all 4 categories)
├── requirements.txt         # Dependencies
├── .gitignore               # Excludes credentials.json, token.pickle, __pycache__
└── README.md
```

---

## Security Notes

- `credentials.json` and `token.pickle` are excluded from version control
- The Gmail scope is read-only (`gmail.readonly`) — the tool cannot send, delete, or modify emails
- API keys are read from environment variables, never hardcoded
- OAuth tokens are stored locally and never transmitted beyond Google's auth infrastructure

---

## Requirements

```
anthropic
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
```

Get an Anthropic API key at [console.anthropic.com](https://console.anthropic.com).
