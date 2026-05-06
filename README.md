# Email Agent Toolkit

**Production-grade AI email management. Five agents. One inbox. Zero missed follow-ups.**

This toolkit processes your Gmail inbox through a multi-agent AI pipeline — classifying emails by urgency, scoring priority, generating ready-to-send draft replies, detecting meeting requests, extracting tasks, tracking follow-ups, and delivering everything as a daily digest or browser dashboard. Built on Claude with structured outputs, prompt caching, and full Google API integration.

| Manual Inbox Management | This Tool |
|-------------------------|-----------|
| Read every email to assess urgency | Classified and scored automatically |
| Write replies from scratch | 2–3 draft options generated per email |
| Miss follow-ups when things get busy | Unanswered threads surfaced daily |
| Manually add meetings to calendar | Meeting details detected and pushed to Calendar |
| Copy action items into a task list | Action items pushed to Google Tasks |
| No memory of who you respond to | Sender reputation builds over time |
| Check email constantly | Morning digest lands in your inbox at 7am |

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Anthropic](https://img.shields.io/badge/Powered%20by-Claude-orange) ![Gmail](https://img.shields.io/badge/Gmail-OAuth2-red)

---

## The Problem

The modern inbox is a productivity tax. The average professional receives 120 emails per day and spends 28% of their working week managing email — not responding to it thoughtfully, but triaging it: opening, skimming, deciding whether it matters, and often closing without acting. Critical threads get buried. Follow-ups slip. Replies are delayed because writing from scratch takes time that busy schedules do not have.

The bottleneck is not the volume of email — it is the cognitive overhead of processing it. Every email requires a judgment call: how urgent is this, what does it need from me, and when? That decision process, multiplied across 120 emails a day, consumes attention that should be going elsewhere.

This toolkit addresses that bottleneck directly. It runs your inbox through a pipeline of specialized AI agents that handle the triage layer automatically — so that your time in email is spent approving and sending responses, not generating them.

---

## What It Does

Given access to your Gmail inbox, the pipeline processes each email through five specialized agents and surfaces everything through an interactive dashboard, morning digest, or terminal session.

**Pipeline output per email:**

| # | Feature | Description |
|---|---------|-------------|
| 1 | Classification | Labeled urgent, action-required, routine, or spam with confidence score |
| 2 | Priority Score | Scored 1–10 using deadline language, sender importance, action item count, and reputation data |
| 3 | Contact Enrichment | Sender's company, role, and domain type inferred and cached — corporate VP scores higher than newsletter |
| 4 | Suggested Subject | Vague subjects rewritten to be searchable (e.g. "follow up" → "Q3 Budget Review: Approval Needed by Friday") |
| 5 | Draft Replies | 2–3 ready-to-send options per email with different tones (Formal, Brief, Casual) |
| 6 | Calendar Detection | Meeting requests identified; date, time, duration, and attendees extracted and pushed to Google Calendar |
| 7 | Task Extraction | Action items pushed to Google Tasks with sender and subject as context |
| 8 | Follow-up Reminders | Sent emails with no reply after 3 days surfaced automatically |
| 9 | Sender Reputation | Response rate tracked per sender; high-engagement contacts scored higher over time |
| 10 | Daily Digest | Priority-sorted summary email delivered to your inbox every morning at 7am |
| 11 | Web Dashboard | Browser UI for reviewing, approving drafts, adding tasks, and creating calendar events |
| 12 | Real-time Watcher | Gmail history API polled for new emails; each one processed immediately on arrival |

**Sample priority table:**

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

## Why This Matters

The productivity case is quantifiable. A professional spending 28% of their week on email — roughly 11 hours — and reducing that to focused decision-making rather than triage reclaims 6–8 hours per week. For executives and consultants billing at $300–500/hour, that is $90,000–$200,000 in recovered capacity per year.

Beyond individual productivity, this project reflects how AI is changing knowledge work. The rote cognitive labor of email triage — classifying, sorting, drafting — is exactly the kind of structured, repeatable task that AI handles well. The judgment calls — what actually matters, what to say, whether to delegate — remain human. This tool handles the former so that professionals can focus on the latter.

The multi-agent architecture is also a deliberate engineering choice. Email processing is not a single task. Classification requires different context than draft generation. Reputation scoring requires historical data that classification does not. Building specialized agents for each concern produces a modular, debuggable system where each agent can be improved independently — the same pattern that enterprise productivity teams are applying to knowledge work automation at scale.

---

## Architecture

The pipeline runs in sequence per email. Each agent receives the output of prior agents as context, allowing downstream scoring and suggestion quality to compound.

```
Gmail Inbox
    │
    ▼
enrich_contact()        ← Company, role, domain type (cached in contacts_cache.json)
    │
    ▼
classify_email()        ← urgent / action-required / routine / spam + confidence
    │
    ▼
score_priority()        ← 1–10 score using classification + contact + reputation
    │
    ▼
suggest_responses()     ← 2–3 draft replies + improved subject line
    │
    ▼
detect_calendar_event() ← Meeting detection + date, time, attendees
    │
    ▼
create_draft()          ← Push selected reply to Gmail Drafts
create_calendar_event() ← Push meeting to Google Calendar
create_tasks()          ← Push action items to Google Tasks
    │
    ▼
export_csv()            ← Timestamped log of all results
followup_tracker()      ← Check SENT for unanswered threads
```

**Agent responsibilities:**

| Agent | File | Input | Output |
|-------|------|-------|--------|
| Contact Enricher | `enrich_contact.py` | Sender string | Company, role, domain type (cached) |
| Email Classifier | `classify_emails.py` | Email content | Classification + confidence + action items |
| Priority Scorer | `score_priority.py` | Email + classification + contact + reputation | Score 1–10 + explanation |
| Response Suggester | `suggest_responses.py` | Email + classification | 2–3 draft replies + suggested subject |
| Calendar Detector | `detect_calendar_event.py` | Email content | Meeting details or `is_meeting_request: false` |
| Reputation Tracker | `reputation.py` | Sender + session results | Response rate + frequency signals |
| Follow-up Tracker | `followup_tracker.py` | Gmail SENT folder | Unanswered threads older than N days |
| Digest Formatter | `digest_email.py` | All pipeline results | Plain-text digest email |

---

## Feature Deep Dive

### Sender Reputation
Every time you save a draft reply, the toolkit records that you responded to that sender. Over time, it builds a per-sender response rate stored in `reputation.json`. Senders you frequently respond to receive a priority boost in the scoring prompt; automated senders with low engagement receive a penalty. The scoring improves with use — the more sessions you run, the more accurately your inbox reflects what actually matters to you.

### Contact Enrichment
The classifier knows that `alex@bigclient.com` is from a client at a corporate domain — but without enrichment it does not know that BigClient is a Fortune 500 company and Alex is a VP. The enricher infers company name, job title (when inferable from name patterns or email conventions), and domain type (personal / corporate / nonprofit / government / automated) from the sender string. Results are cached in `contacts_cache.json` so each contact is only looked up once across all sessions.

### Follow-up Reminders
The tracker reads your SENT folder and checks whether each sent thread has received a reply. Any thread with only one message — your original send — and older than 3 days is flagged. Results appear in the terminal session summary, the web dashboard's Follow-ups tab, and the morning digest. Nothing falls through the cracks.

### Web Dashboard
A Flask-based browser UI that shows the full priority-sorted inbox with color-coded cards by classification (red for urgent, orange for action-required, blue for routine, grey for spam). Each card surfaces the priority explanation, suggested subject line, action items with a one-click Tasks button, meeting detection with a Calendar button, and 2–3 draft replies with Save as Draft buttons. A dedicated Follow-ups tab shows unanswered sent emails and inbox emails still waiting for a response — all in one place.

### Daily Digest
A scheduled email delivered to your own inbox every morning at 7am. Includes a priority summary table, per-email details with action items and suggested subjects, a follow-up reminders section, and a direct link to launch the dashboard. Configured with a single shell command — no cron knowledge required.

---

## Engineering Decisions

**Multi-agent design over a single prompt.** A single prompt generating classification, scoring, drafts, and calendar detection simultaneously creates fragility — one malformed section corrupts the entire response. Specialized agents produce isolated outputs that feed forward as structured context. Failures are localized, debuggable, and fixable without touching other agents.

**Structured JSON schemas with `output_config`.** Every agent returns a validated JSON object with a strict schema enforced at the API level. This eliminates parsing fragility, ensures downstream agents always receive well-formed input, and makes every output composable. The schemas also enforce consistency — confidence scores and classifications are always present by design, not by convention.

**Prompt caching on system prompts.** Each agent sends its system prompt with `cache_control: ephemeral`. For 10 emails, this means the system prompt is processed once and cached for all subsequent calls — reducing per-email token cost by roughly 10× on repeated runs.

**Reputation as a feedback loop.** Most email tools treat every email from a sender as independent. Reputation tracking introduces memory: the tool learns from your behavior over time. A sender you never respond to gradually loses priority weight. A client you always reply to within an hour gains it. This is the difference between a static classifier and a system that adapts to its user.

**No Pub/Sub for real-time mode.** Gmail push notifications via Google Cloud Pub/Sub require a public-facing endpoint and additional Cloud infrastructure. The watcher instead polls the Gmail history API using `historyId` as a cursor — detecting new messages since the last poll without any cloud setup. For a personal productivity tool, polling every 5 minutes is operationally equivalent to real-time.

**Flask for the dashboard, no frontend framework.** The dashboard is a personal tool used by one person. A React frontend would add build tooling, dependency management, and deployment complexity with no benefit at this scale. Server-rendered Jinja2 templates with inline CSS and 20 lines of vanilla JavaScript deliver the same UX in a fraction of the code.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language Model | Anthropic Claude (`claude-opus-4-7`) |
| Agent Orchestration | Python — custom pipeline |
| Email API | Google Gmail API v1 — OAuth2 |
| Calendar API | Google Calendar API v3 |
| Tasks API | Google Tasks API v1 |
| Web Dashboard | Flask + Jinja2 |
| Output Formats | CSV (timestamped logs), plain-text digest email |
| Auth | google-auth-oauthlib — token persisted in `token.pickle` |
| Test Suite | pytest — 100 tests, all mocked |
| Runtime | Python 3.9+ |

---

## Getting Started

**Quick start (no credentials needed):**

```bash
git clone https://github.com/kingabsalom/email-agent-toolkit
cd email-agent-toolkit
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python3 main.py
```

Runs against the included `sample_emails.json` — five realistic test emails covering all four classification categories. No Gmail setup required.

---

## Gmail Setup (one-time)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable the **Gmail API**, **Google Calendar API**, and **Google Tasks API**
3. Create OAuth2 credentials (Desktop app) → download as `credentials.json`
4. Place `credentials.json` in the project directory
5. Run `python3 main.py` — a browser window opens for authorization
6. `token.pickle` is saved automatically; you will not be prompted again

---

## Usage

**Interactive terminal session:**
```bash
python3 main.py
```
Processes your last 48 hours of inbox. Prompts you to save drafts, add tasks, and create calendar events for each email. Exports a timestamped CSV at the end.

**Browser dashboard:**
```bash
python3 run_dashboard.py
```
Processes your inbox and opens the web UI at `http://127.0.0.1:5000`. All actions are available as one-click buttons. A Follow-ups tab surfaces unanswered threads and action-required emails.

**Daily digest (automated):**
```bash
./setup_cron.sh
```
Adds a cron job that runs at 7am every day and emails a priority-sorted digest to your inbox. Run once to configure.

**Real-time watcher:**
```bash
python3 watch.py                    # poll every 5 minutes
python3 watch.py --interval 120     # poll every 2 minutes
```

**Run tests:**
```bash
python3 -m pytest tests/ -v
```
100 tests, all external APIs mocked — no credentials or API keys required.

---

## Project Structure

```
email-agent-toolkit/
├── main.py                    # Interactive pipeline orchestrator
├── run_dashboard.py           # Processes inbox + launches Flask dashboard
├── run_digest.py              # Non-interactive pipeline for cron/scheduled runs
├── watch.py                   # Real-time Gmail poller
├── setup_cron.sh              # Adds 7am daily cron job
├── gmail_reader.py            # Gmail, Calendar, Tasks OAuth2 auth + service builders
├── classify_emails.py         # Agent: classify as urgent / action-required / routine / spam
├── score_priority.py          # Agent: score 1–10 with contact + reputation context
├── suggest_responses.py       # Agent: generate draft replies + suggested subject
├── detect_calendar_event.py   # Agent: identify meeting requests and extract details
├── enrich_contact.py          # Infer company, role, domain type — cached per address
├── reputation.py              # Track sender response rates across sessions
├── followup_tracker.py        # Scan SENT folder for unanswered threads
├── create_draft.py            # Push draft reply to Gmail Drafts
├── create_calendar_event.py   # Push meeting to Google Calendar
├── create_tasks.py            # Push action items to Google Tasks
├── digest_email.py            # Format and send daily digest email
├── export_csv.py              # Write timestamped CSV log of all results
├── dashboard.py               # Flask web app routes
├── templates/index.html       # Dashboard UI — inbox + follow-ups tabs
├── tests/                     # 100 pytest tests — all APIs mocked
├── sample_emails.json         # Offline test data (5 emails, all 4 categories)
└── requirements.txt
```

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | Complete | Core pipeline — classify, score, suggest, CSV export, 100-test suite |
| Phase 2 | Complete | Auto-draft to Gmail, scheduled digest, subject line suggestions |
| Phase 3 | Complete | Calendar detection, task extraction, follow-up reminders, contact enrichment |
| Phase 4 | Complete | Sender reputation, real-time watcher, web dashboard with Follow-ups tab |
| Phase 5 | Planned | Bills and sales-opportunity classification labels |
| Phase 6 | Planned | Thread summarization — condense 20-email chains to 3 bullet points |
| Phase 7 | Vision | Tone adjustment — rewrite a draft to be more or less formal before sending |
| Phase 8 | Long-term | CRM integration — sync contact enrichment and interaction history to HubSpot or Salesforce |

---

## Limitations

This toolkit is designed as a triage accelerator, not a replacement for human judgment on email communication.

**Draft quality requires review.** Generated replies are starting points, not finished messages. They reflect the content of the email but not the full context of your relationship with the sender, your organization's voice, or nuances known only to you. All drafts should be reviewed before sending.

**Classification confidence is not certainty.** The classifier returns a confidence score, but a 95% confidence URGENT classification is still wrong 1 in 20 times at scale. Low-confidence classifications warrant additional scrutiny.

**Contact enrichment is inference, not lookup.** The enricher infers company and role from the sender's email address and display name — it does not query a contact database. For senders with ambiguous domains or unusual naming conventions, the enrichment may be incomplete.

**Reputation requires time to build.** The reputation system has no signal until you have run several sessions. Priority scoring relies on classification and contact enrichment alone for the first few runs. The reputation layer becomes meaningful after 2–3 weeks of regular use.

**Gmail OAuth scope is broader than read-only.** To support draft creation, calendar events, and task extraction, the OAuth consent screen requests compose, calendar, and tasks scopes in addition to read-only. Review the scope list in `gmail_reader.py` if you prefer to limit access.

---

## About

Built by an MBA candidate at Johns Hopkins Carey Business School, studying Competitive Strategy and applying AI engineering to knowledge work workflows. This project demonstrates multi-agent systems design applied to a high-frequency, high-friction personal productivity problem — the kind of tooling that enterprise software teams and AI-native startups are building internally.

[LinkedIn](https://linkedin.com/in/alexanderjstephens) — open to conversations about AI in productivity, strategy, and product.

---

*Draft replies are AI-generated starting points intended for human review before sending. Not intended for use without review in sensitive or high-stakes communication contexts.*
