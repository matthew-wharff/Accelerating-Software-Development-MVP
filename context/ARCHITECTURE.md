# Architecture

High-level reference for agents. Not an implementation spec — for orientation and boundary enforcement.

## Pipeline Order

```
Spec Clarifier → Architect → Coder (Ralph Loop) → e2b Sandbox
    → [Test Writer | Security Reviewer | Code Quality | DevOps] (parallel)
    → Synthesis → revision loop (max 2x) → GitHub MCP → output
```

## Module Boundaries

| Module | File | Responsibility |
|---|---|---|
| Spec Clarifier | `agents/spec_clarifier.py` | Asks 3–5 targeted questions to resolve ambiguities before any code is written |
| Architect | `agents/architect.py` | Produces 3 artifacts: `shared_dependencies.md`, interface definitions, ordered task queue. Runs a feedback loop after each Coder task. |
| Coder | `agents/coder.py` | Implements one file per invocation using the Ralph Loop. Stateless between tasks. |
| Test Writer | `agents/test_writer.py` | Generates pytest unit + integration tests. Critic — uses Haiku. |
| Security Reviewer | `agents/security_reviewer.py` | OWASP Top 10 review. Critic — uses Haiku. |
| Code Quality | `agents/code_quality.py` | PEP 8, style, structure review. Critic — uses Haiku. |
| DevOps | `agents/devops.py` | Produces Dockerfile, CI/CD config, docker-compose.yml. Uses Sonnet. Runs in parallel with critics. |
| Synthesis | `agents/synthesis.py` | Merges all critic feedback into one prioritized action list. Writes `SYNTHESIS_REPORT.md`. |
| Pipeline | `graph/pipeline.py` | LangGraph graph definition — nodes, edges, conditional routing |
| State Schema | `state/schema.py` | `PipelineState` TypedDict — paths and compact logs only, never file contents |

## Models

| Agent | Model |
|---|---|
| Architect, Coder, Synthesis, DevOps | `claude-sonnet-4-20250514` |
| Test Writer, Security Reviewer, Code Quality | `claude-haiku-4-5-20251001` |

## Data Flow

Each agent receives only the context relevant to its job:

**Spec Clarifier** — receives: raw project brief. Produces: `{question: answer}` dict.

**Architect** — receives: clarified brief + Spec Clarifier answers. Produces: `shared_dependencies.md` (written to disk), interface definitions (written to disk), ordered task queue (in state).

**Coder (per task)** — receives: current task description, `shared_dependencies.md` (from disk), relevant interface definitions, exported signatures of dependency files only. Does NOT receive: full spec, full source of prior files, conversation history, critic feedback.

**e2b Sandbox** — receives: `/output/` file tree. Produces: `{stdout, stderr, exit_code}` stored in state.

**Test Writer** — receives: implementation files + interface defs + `shared_dependencies.md` + e2b output. Does NOT receive: security findings, quality notes, Dockerfile.

**Security Reviewer** — receives: implementation files + `shared_dependencies.md` + env var definitions. Does NOT receive: test files, quality notes, e2b output.

**Code Quality** — receives: implementation files + `CONVENTIONS.md`. Does NOT receive: test files, security findings, DevOps config.

**DevOps** — receives: file tree + `shared_dependencies.md` + `CONVENTIONS.md`. Does NOT receive: implementation source code, any critic output.

**Synthesis** — receives: all three critic outputs from state. Produces: structured JSON action list + `SYNTHESIS_REPORT.md` on disk.

**Coder (revision pass)** — receives: `SYNTHESIS_REPORT.md` (from disk) + fresh task context. Does NOT receive: raw critic output.

## Key Constraints

| Constraint | Value |
|---|---|
| Max revision cycles | 2 |
| Coder retry limit before Architect escalation | 3 failures |
| e2b sandbox timeout | 30 seconds |
| State values | Paths and compact logs — never file contents |
| Agent handoffs | Structured markdown report files on disk — never raw LLM transcripts |
| Stable context files | `CONVENTIONS.md`, `shared_dependencies.md`, `ARCHITECTURE.md` — injected into every agent call |

## Filesystem Layout

```
/output/        generated source code — gitignored
/context/       stable context files injected into every agent call
agents/         one .py file per agent
graph/          LangGraph pipeline definition
state/          PipelineState schema
prompts/        prompt template strings
tests/          unit + integration tests
scripts/        utilities (logger, file_writer)
```

## Revision Loop Routing

After Synthesis:
- `has_critical_issues = true` AND `revision_count < 2` → route back to Coder with fresh context + `SYNTHESIS_REPORT.md`
- `has_critical_issues = false` OR `revision_count >= 2` → route to output / GitHub MCP
