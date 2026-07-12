# 🧠 DSA Coach — AI-Powered Interview Preparation Agent

An agentic AI system built with **LangGraph + LangChain** that coaches you
through daily DSA practice using real LeetCode problems.

## What it does

1. **You pick topics** — type "Array, DP, Graph" and it fuzzy-matches to the dataset's 63 official tags
2. **It picks 5 problems** — 2 Easy + 2 Medium + 1 Hard from 2,641 LeetCode problems (never repeats)
3. **You describe your approach** — plain English, as detailed as you want
4. **It generates code** — C++ or Python, based ONLY on your described logic (nothing extra)
5. **You test on LeetCode** — copy the code, paste it, run it yourself
6. **You report back** — success → next question. Failure → paste the error
7. **It analyses the failure** — approach issue vs implementation bug, with specific fixes
8. **You choose** — fix it yourself or let the AI auto-fix within your approach
9. **Session summary** — tracks all 5 problems, attempts, and outcomes

## Tech Stack

- **LangGraph** — StateGraph with conditional edges, iterative loops, Human-in-the-Loop (`interrupt()`)
- **LangChain** — LLM calls, prompt templates, message management
- **Groq (free)** — `llama-3.3-70b-versatile` for code generation and analysis
- **Streamlit** — full web UI with progress tracking, code display, session history
- **Dataset** — [newfacade/LeetCodeDataset](https://github.com/newfacade/LeetCodeDataset) v0.3.1 (2,641 problems)

## LangGraph Workflow

```
START → QuestionPicker → QuestionDisplay [HITL] → UserApproach [HITL]
     → CodeGenerator → LeetCodeHITL [HITL]
         ├── success → NextQuestion → (loop or SessionSummary → END)
         └── failure → ApproachJudge
                          ├── approach_ok   → CodeAnalyser [HITL]
                          │                      ├── auto_fix  → CodeGenerator (loop)
                          │                      └── self_edit → LeetCodeHITL (loop)
                          └── approach_wrong → ApproachWrong [HITL] → CodeGenerator
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/dsa-coach
cd dsa-coach
uv venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv add -r requirements.txt
```

### 2. Get the dataset

Download `LeetCodeDataset-v0.3.1-train.jsonl.gz` from:
https://github.com/newfacade/LeetCodeDataset/tree/main/data

Place it in the project root (same folder as `app.py`).

### 3. Set up API keys

Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at: https://console.groq.com

### 4. Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501

## Project Structure

```
dsa-coach/
├── app.py                              ← Streamlit UI (all screens)
├── graph.py                            ← LangGraph StateGraph + routers
├── nodes.py                            ← All 10 node functions
├── state.py                            ← DSAState TypedDict definition
├── dataset.py                          ← Dataset loading, filtering, selection
├── requirements.txt
├── .env                                ← API keys (not committed)
├── .gitignore
├── seen_ids.json                       ← Auto-created: tracks seen problems
└── LeetCodeDataset-v0.3.1-train.jsonl.gz ← Dataset (download separately)
```

## Features

- **Fuzzy topic matching** — "dp" → "Dynamic Programming", "bfs" → "Breadth-First Search"
- **Never repeats problems** — `seen_ids.json` tracks every problem across sessions
- **Language choice** — C++ or Python code generation
- **Constrained code generation** — LLM is strictly prohibited from adding logic you did not describe
- **Approach judge** — distinguishes implementation bugs from conceptual flaws
- **Iterative retry loop** — up to configurable attempts per problem
- **Session history** — sidebar shows all completed problems in real time

## Phase 2 (planned)

- Voice input via Whisper API
- Local code execution against dataset test cases (no LeetCode needed)
- Progress tracking dashboard across multiple sessions
- Topic-based weak area identification
