# AI Day 7 — Market Intelligence Agent (Production-Grade LangGraph System)

## What this is
A production-grade LangGraph intelligence agent built as part of a 20-day AI learning curriculum. The agent identifies critical market gaps across three domains, enriches findings with live web search, pauses for human approval, and persists all runs to SQLite.

## Live Demo
[Link to be added after Streamlit Cloud deployment]

## Architecture

```
[Streamlit UI]
      ↓
[Domain Selector] — AI Products / Startup Funding / PM Jobs
      ↓
[Node 1: Load Data]         → reads JSON dataset + SQLite run history
      ↓
[Node 2: Find Gaps]         → identifies top 3 gaps by scoring logic
      ↓
[Node 3: Enrich Gaps]       → web search for each gap (live context)
      ↓
[Node 4: Classify Severity] → LLM classifies CRITICAL / MODERATE / HEALTHY
      ↓
[Conditional Edge]          → branches based on severity
      ↙           ↓           ↘
[Escalate]   [Monitor]   [Log Healthy]
      ↘           ↓           ↙
[Node 5: HITL]              → agent pauses, shows findings, waits for approval
      ↓
[Node 6: Recommend]         → generates strategic report if approved
      ↓
[SQLite]                    → saves every run regardless of approval
```

## Three Intelligence Domains

### 🤖 AI Product Intelligence
Identifies underserved AI product categories — large markets with few good products.

**Gap logic:** Low coverage score = big gap
**Example finding:** AI for Elderly Care — $2.4B market, only 2 competitors, coverage score 1.2

---

### 💰 Startup Funding Gaps
Identifies problem spaces with large markets but minimal startup funding.

**Gap logic:** Low funding gap score = big gap
**Example finding:** Mental health for rural India — $2.1B market, only 3 funded startups

---

### 💼 PM Job Market Intelligence
Identifies PM skills in high demand but low supply.

**Gap logic:** High demand score minus supply score = big gap
**Example finding:** AI Product Management — demand 9.4, supply 2.1, 38% salary premium

## What makes this production-grade

### Separation of concerns
```
agent/
├── state.py      ← what data flows through the agent
├── nodes.py      ← what each step does
├── graph.py      ← how steps connect
└── database.py   ← how data is saved and loaded
app.py            ← what the user sees
```

Each file has one job. Adding a new node or domain doesn't require touching every file.

### Web search enrichment
Mock data tells you where gaps exist. Web search tells you what's happening there right now. The agent combines both for actionable, current recommendations.

### Human-in-the-loop
Agent pauses after severity classification. Shows enriched findings. Waits for explicit human approval before generating the final report. Cancelled runs are still saved — knowing what users rejected is as valuable as what they approved.

### SQLite persistence
Every run saved to `intelligence.db`. Second run on the same domain loads previous findings. Agent builds on prior analysis rather than starting fresh.

## PM mental models demonstrated

- **State = shared whiteboard** — every node reads from and writes to one shared dictionary
- **Nodes = one job each** — separation of concerns makes debugging and iteration fast
- **Conditional edges = product routing decisions** — severity classification determines which path the agent takes
- **HITL = trust boundary** — placed at the point where actions become consequential
- **Persistence = what turns a demo into a product** — demos reset, products accumulate knowledge
- **Mock data + web enrichment = production-realistic** — structured data + live context is how real systems work
- **Saving cancellations = product insight** — rejected recommendations reveal user preferences

## Tech stack
- Python 3.13
- LangGraph
- LangChain + ChatOpenAI (gpt-4o-mini)
- OpenAI web search (gpt-4o-mini-search-preview)
- SQLite (built into Python)
- Streamlit
- python-dotenv

## File structure
```
ai_d7/
├── venv/
├── .env
├── intelligence.db          ← auto-created on first run
├── data/
│   ├── ai_products.json     ← 20 AI product categories with scores
│   ├── startup_funding.json ← 20 problem spaces with funding data
│   └── pm_jobs.json         ← 20 PM skills with demand/supply scores
├── agent/
│   ├── __init__.py
│   ├── state.py
│   ├── nodes.py
│   ├── graph.py
│   └── database.py
├── app.py
└── README.md
```

## How to run locally

```bash
# Clone the repo
git clone https://github.com/nishakaimal02-cpu/ai_d7.git
cd ai_d7

# Create virtual environment
python3 -m venv venv

# Install dependencies
venv/bin/pip install langgraph langchain langchain-openai openai python-dotenv streamlit pandas

# Add your API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the app
venv/bin/streamlit run app.py
```

## How to test persistence
1. Select any domain and run the agent
2. Approve the recommendation
3. Run the same domain again
4. Node 1 will show previous run history loaded
5. Check the sidebar for full run history

