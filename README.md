# Intelligent Spam Detection Agent

A multi-agent, tool-augmented, memory-enabled spam/phishing detection system.
Built per the proposed architecture: Manager → Content, Link/Domain, Behavior,
Evidence agents → Critic agent → Reporter agent, with SQLite persistent memory
and a feedback-driven adaptation loop.

## Why it works with zero setup

Every agent has a **built-in rule-based / heuristic mode**, so the whole
pipeline runs immediately with `pip install` only — no API keys required.

If you add API keys, the system automatically upgrades itself:

| Env var          | Unlocks                                              |
|-------------------|-------------------------------------------------------|
| `OPENAI_API_KEY`  | LLM-based nuanced content analysis (Content Agent)    |
| `TAVILY_API_KEY`  | Real-time web search for domain/campaign reputation (Link & Evidence Agents) |

Without keys, those agents silently fall back to heuristics — nothing breaks.

## Install

```bash
cd spam_detection_agent
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

`requirements.txt` only hard-requires the standard library + `python-dotenv`.
`openai`, `tavily-python`, and `gradio` are optional — install them only if
you want those upgrades / the web UI.

## Configure (optional)

Copy `.env.example` to `.env` and fill in keys if you have them:

```bash
cp .env.example .env
```

## Run — CLI

Analyze a single message:

```bash
python main.py analyze --text "URGENT! Your account will be suspended. Click http://bit.ly/xyz123 now to verify!" --sender "promo@totally-legit-bank.tk" --channel email
```

Interactive mode (keeps asking for messages, lets you give feedback):

```bash
python main.py interactive
```

Give feedback on a past decision (teaches the system):

```bash
python main.py feedback --decision-id 3 --type false_positive --comment "This was a real order confirmation"
```

Show current sender/domain risk profiles and thresholds:

```bash
python main.py stats
```

## Run — Web UI (optional, needs `pip install gradio`)

```bash
python app_gradio.py
```

Opens a local Gradio app with a text box, metadata fields, a rendered
security report, and 👍 Correct / 👎 False Positive / 👎 False Negative
feedback buttons that feed straight back into the adaptation loop.

## Architecture

```
                    ┌──────────────┐
   message  ───────▶│ Manager Agent│
                    └──────┬───────┘
             ┌─────────────┼──────────────┬───────────────┐
             ▼             ▼              ▼               ▼
      Content Agent   Link/Domain    Behavior Agent   Evidence Agent
      (text patterns)  Agent (URLs,  (sender/metadata) (web search for
                        domain rep)                     borderline cases)
             └─────────────┴──────────────┴───────────────┘
                                  ▼
                            Critic Agent
                     (aggregates + verifies + scores)
                                  ▼
                           Reporter Agent
                (label, confidence, reasons, action, report)
                                  ▼
                         SQLite persistent memory
                   (messages, decisions, feedback,
                    sender_profiles, domain_profiles)
                                  ▼
                      Feedback → Adaptation module
                (adjusts thresholds + sender/domain risk)
```

## Database

SQLite file `spam_agent.db` is created automatically on first run, with
tables: `messages`, `decisions`, `feedback`, `sender_profiles`,
`domain_profiles`, `thresholds`.

## Files

```
spam_detection_agent/
├── README.md
├── requirements.txt
├── .env.example
├── config.py              # settings, thresholds, API key detection
├── db.py                  # SQLite schema + helper functions
├── adaptation.py           # feedback-driven threshold/profile updates
├── main.py                # CLI entry point
├── app_gradio.py          # optional web UI
├── sample_data/
│   └── sample_messages.json
└── agents/
    ├── __init__.py
    ├── manager.py          # orchestrates the pipeline
    ├── content_agent.py    # text/pattern analysis (+ optional LLM)
    ├── link_agent.py       # URL/domain extraction + reputation
    ├── behavior_agent.py   # sender/behavioral analysis
    ├── evidence_agent.py   # web search for borderline cases
    ├── critic_agent.py     # aggregates, verifies, scores
    └── reporter_agent.py   # builds final report, recommends action
```

## Extending

- Swap the heuristic Content Agent scorer for a trained scikit-learn/XGBoost
  classifier by editing `agents/content_agent.py::score_with_ml`.
- Add a new channel (e.g. WhatsApp) — the pipeline is channel-agnostic;
  just pass `channel="whatsapp"` into `analyze_message`.
- Wrap `manager.analyze_message` as a FastAPI endpoint to expose it as an
  MCP tool or REST API for n8n / Gmail automation.
