# Multi-Agent Dev Assistant — MVP

> A LangGraph pipeline that turns a plain-English project brief into scaffolded code, then has a second AI agent review it. Weekend MVP proving the core **Coder → Critic → File output** loop.

![Status](https://img.shields.io/badge/status-MVP-yellow)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What This Does

Give it a project brief in plain English. It generates a working code file and has an independent AI critic review the output for bugs, style issues, and missing edge cases.

**Example input:**
> Build a Python REST API for a task manager with SQLite. Include endpoints for create, read, update, delete tasks. Use FastAPI and include basic input validation.

**Output:**
- Generated Python source file written to `/output/`
- Critic review written to `/output/feedback_*.md`

This is the MVP — a deliberately minimal version that proves the orchestration pattern works end-to-end. The full system (not yet public) adds a planning agent, dependency-ordered task decomposition, parallel code reviewers, sandboxed execution, and automated GitHub integration.

---

## Demo

*(Add a screenshot or GIF of a pipeline run here — `/docs/demo.gif`)*

---

## Why This Design

The core design constraint is **context isolation**. Research on multi-file code generation shows a large accuracy gap between single-function tasks (~87%) and multi-file tasks (~19%) — and the gap is caused by context pollution, not model capability. The model gets confused when it's asked to hold too much in its head at once.

Three rules shape every architectural decision:

1. **Decompose before generating.** The Coder receives one scoped task at a time, not a monolithic project spec.
2. **Isolate by default.** Each agent invocation gets only what it needs for its current job — no accumulated history, no sibling agents' output.
3. **Compress at boundaries.** State holds file paths, not file contents. Generated code is written to disk and referenced by path, never re-injected into context.

Even in this MVP, the Coder receives a scoped task dict, not the full conversation history. Establishing that habit from the first line of code is the whole point.

---

## Architecture

```
    ┌─────────────────┐
    │ Project Brief   │
    └────────┬────────┘
             ▼
    ┌─────────────────┐     ┌──────────────────┐
    │  Coder Agent    │────▶│ /output/*.py     │
    │  (Claude Sonnet)│     │ (written to disk)│
    └────────┬────────┘     └──────────────────┘
             ▼
    ┌─────────────────┐     ┌──────────────────┐
    │  Critic Agent   │────▶│ /output/         │
    │  (Claude Haiku) │     │ feedback_*.md    │
    └─────────────────┘     └──────────────────┘
```

**Key design choices:**

| Decision | Why |
|---|---|
| LangGraph over CrewAI | The full pipeline has conditional revision loops — LangGraph handles cycles natively as a state machine |
| Claude Sonnet for Coder, Haiku for Critic | Sonnet for generation, Haiku for review — ~10x cost reduction on review passes with negligible quality impact |
| File paths in state, not file contents | Keeps the state object small and prevents context accumulation across nodes |
| Separate Critic agent, not self-review | Independent review produces better signal than a single agent critiquing its own output |

---

## Tech Stack

- **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/)
- **LLMs:** Claude Sonnet 4 (Coder), Claude Haiku 4.5 (Critic) via the [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- **Language:** Python 3.11+
- **Dev tooling:** pyenv, venv, Ruff (lint + format), pytest

---

## Running Locally

### Prerequisites

- Python 3.11+ (via [pyenv](https://github.com/pyenv/pyenv) recommended)
- An [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
# Clone and enter the repo
git clone git@github.com:matthew-wharff/multi-agent-dev-assistant-mvp.git
cd multi-agent-dev-assistant-mvp

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Then edit .env and add your ANTHROPIC_API_KEY
```

### Run the pipeline

```bash
python -m graph.pipeline
```

Generated code and critic feedback will appear in `/output/`.

### Run tests

```bash
pytest -v
```

---

## Project Structure

```
agents/          # Individual agent implementations
  coder.py       # Generates code from a task description (Sonnet)
  critic.py      # Reviews generated code for bugs and quality (Haiku)
graph/
  pipeline.py    # LangGraph graph wiring: Coder → Critic → Output
state/
  schema.py      # Shared state schema — holds file paths, not contents
scripts/
  file_writer.py # Utility for writing files to /output/ safely
  logger.py      # Project-wide logger (never use print())
tests/           # pytest tests
output/          # Generated code lands here (gitignored)
```

---

## What's Next

This MVP proves the orchestration pattern. The full system adds:

- **Spec Clarifier Agent** — interrogates the brief for ambiguities before any code is written
- **Architect Agent** — produces a dependency-ordered task queue and an interface manifest, so the Coder implements against stable contracts
- **Ralph Loop for the Coder** — one task at a time with a fresh context window per task
- **Parallel Critic Trio** — Test Writer + Security Reviewer + Code Quality running simultaneously via LangGraph's `Send` API
- **Synthesis Agent** — a context firewall that compresses three critic outputs into one prioritized action list
- **DevOps Agent** — Dockerfile, CI/CD, `.env.example` generated from the spec
- **e2b sandbox execution** — generated code runs in an isolated environment before critics review it
- **GitHub MCP integration** — the final pipeline creates a real GitHub repo and commits the generated code

The full repo will go public once Phase 1B (hardening and security audit) is complete.

---

## Development Process

This project was built with heavy use of [Claude Code](https://claude.com/claude-code) as an AI pair programmer. I want to be direct about what that means:

- **I designed:** the overall agent architecture, context isolation strategy, state schema, and LangGraph topology. These decisions are mine and I can defend every one of them.
- **Claude Code assisted with:** boilerplate implementation, test scaffolding, and debugging.
- **I reviewed and revised:** every agent prompt, the state management logic, and all error handling before committing.

Using AI tooling effectively is itself a skill I'm deliberately developing through this project. The interesting questions are *why* each architectural choice was made — not who typed the code.

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Contact

Matthew Wharff
LinkedIn: [link text](linkedin.com/in/matthew-wharff)

*(Add your name, portfolio link, LinkedIn, or email here)*
