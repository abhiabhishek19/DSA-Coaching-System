# 🧠 DSA Coach — Agentic AI-Powered Interview Preparation

A personal DSA preparation assistant built with **LangGraph + LangChain + Groq**. You describe your approach in plain English — the agent generates code from it, you test it on LeetCode yourself, and if it fails, the agent analyses what went wrong and helps you fix it.

---

## How It Works

1. **Pick your topics** — type topics like "Array, Dynamic Programming, Graph" and the system fuzzy-matches them to the dataset's official tags
2. **Choose your language** — C++ or Python
3. **Get 5 curated problems daily** — selected from a curated LeetCode dataset by difficulty (Easy / Medium / Hard), problems never repeat across sessions
4. **Describe your approach** — plain English; the AI generates code based **only** on your described logic, nothing more
5. **Test on LeetCode yourself** — copy the generated code, paste it into LeetCode's editor, and run it
6. **Report the result** — passed → next question; failed → paste the error output
7. **Get targeted analysis** — the agent classifies whether your approach is conceptually flawed or just has an implementation bug, then gives line-level debugging feedback
8. **Choose your fix** — fix it yourself, let the AI auto-fix within your approach, or revise your approach entirely
9. **Session summary** — shows all attempted, solved, and skipped questions at the end

---

## LangGraph Workflow

```
START
  │
  ▼
QuestionPickerNode         — loads dataset, fuzzy-matches topics, selects 5 problems
  │
  ▼
QuestionDisplayNode        — renders the problem; waits for user to read [HITL]
  │
  ▼
UserApproachNode           — collects approach text or skip signal [HITL]
  │
  ├── __SKIP__ ──────────────────────────────────────────────► NextQuestionNode
  │
  └── approach text
        │
        ▼
      CodeGeneratorNode    — LLM generates C++ or Python from approach only
        │
        ▼
      LeetCodeHITLNode     — user tests on LeetCode, reports result [HITL]
        │
        ├── success ──────────────────────────────────────────► NextQuestionNode
        │
        └── failure (+ pasted error)
              │
              ▼
            ApproachJudgeNode     — classifies: conceptual flaw vs implementation bug
              │
              ▼  (always, regardless of verdict)
            CodeAnalyserNode      — root-cause analysis + fix recommendation [HITL]
              │
              ├── self_edit    ──► LeetCodeHITLNode   (user edits on LeetCode)
              ├── auto_fix     ──► CodeGeneratorNode  (AI regenerates with fix context)
              └── revise_approach ► ApproachWrongNode [HITL] ──► CodeGeneratorNode

NextQuestionNode
  ├── more questions ──► QuestionDisplayNode  (loop)
  └── all done       ──► SessionSummaryNode [HITL] ──► END
```

**Key design decisions:**
- `ApproachJudgeNode` always routes to `CodeAnalyserNode` — the user sees the full code analysis regardless of whether the approach is flawed or just buggy
- Skipping a question bypasses `CodeGeneratorNode` and `LeetCodeHITLNode` entirely and goes straight to `NextQuestionNode` — skipped questions are tracked separately from attempted ones
- `CodeGeneratorNode` receives previous analysis as context on auto-fix retries, staying strictly within the user's original approach

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agentic workflow | LangGraph (StateGraph, MemorySaver, interrupt) |
| LLM | Groq — `llama-3.3-70b-versatile` (free tier) |
| LLM framework | LangChain, LangChain-Groq |
| UI | Streamlit |
| Dataset | [newfacade/LeetCodeDataset](https://github.com/newfacade/LeetCodeDataset) v0.3.1 |
| Session memory | LangGraph MemorySaver (in-memory checkpointing) |
| Environment | Python 3.9+, UV package manager |

---

## Project Structure

```
dsa-coach/
├── app.py                                    ← Streamlit UI — all screens and HITL handling
├── graph.py                                  ← LangGraph StateGraph, nodes, edges, routers
├── nodes.py                                  ← All 10 node functions with full logic
├── state.py                                  ← DSAState TypedDict definition
├── dataset.py                                ← Dataset loading, fuzzy matching, question selection
├── requirements.txt
├── .env                                      ← API keys (not committed)
├── .gitignore
├── seen_ids.json                             ← Auto-created; tracks seen problems across sessions
└── LeetCodeDataset-v0.3.1-train.jsonl        ← Dataset file (download separately — see Setup)
```

---

## Setup

### 1. Clone and initialise

```bash
git clone https://github.com/YOUR_USERNAME/dsa-coach
cd dsa-coach
uv init .
uv venv
```

Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
uv add -r requirements.txt
```

### 3. Download the dataset

Download `LeetCodeDataset-v0.3.1-train.jsonl` (or the `.jsonl.gz` version) from:

> https://github.com/newfacade/LeetCodeDataset/tree/main/data

Place it in the project root — the same folder as `app.py`. Both plain `.jsonl` and gzipped `.jsonl.gz` are supported automatically.

### 4. Create your `.env` file

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at: https://console.groq.com

### 5. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Features

- **Fuzzy topic matching** — "dp" resolves to "Dynamic Programming", "bfs" to "Breadth-First Search", and so on across all dataset tags
- **No repeated problems** — `seen_ids.json` tracks every problem shown across all sessions; a reset button clears it when needed
- **Constrained code generation** — the LLM is instructed to implement only what you described, adding `// TODO` comments for any parts you left unspecified
- **Language choice** — C++ or Python per session; C++ uses LeetCode's standard class structure
- **Skip without penalty** — skipped questions bypass code generation entirely and are tracked separately in the session summary
- **Three-way fix choice** — after a failure analysis: fix it yourself, auto-fix within your approach, or scrap the approach and start fresh
- **Session summary** — attempted, solved, and skipped questions shown separately with your approach recorded for each

---

## Phase 2 (Planned)

- Voice input via Whisper API for approach description
- Local code execution against dataset test cases (no LeetCode needed)
- Multi-session progress tracking and weak-area identification by topic
- Difficulty adaptation based on historical performance
