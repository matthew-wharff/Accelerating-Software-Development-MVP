# Conventions

Coding standards for every file generated or modified in this project.

## Python Version
Python 3.11+. Never use the system Python — always use the pyenv-managed version.

## Import Order
Three groups, separated by a single blank line:
1. Standard library
2. Third-party packages
3. Local modules (`from agents.`, `from state.`, `from utils.`, etc.)

No blank lines within a group. One blank line between groups.

## Naming
| Construct | Convention | Example |
|---|---|---|
| Functions | `snake_case` | `def extract_interface()` |
| Variables | `snake_case` | `task_queue` |
| Classes | `PascalCase` | `class PipelineState` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_REVISIONS = 2` |
| Modules / files | `snake_case` | `spec_clarifier.py` |

## Error Handling
- Use explicit `try/except` with typed exceptions: `except ValueError as e:`
- Never use bare `except:` or `except Exception:` without re-raising or logging
- Propagate errors upward; do not silently swallow them
- On unrecoverable errors, raise with a descriptive message

## Docstrings
Google style on all public functions and classes.

```python
def call_claude(task: Task, manifest: str) -> str:
    """Call Claude with scoped context for a single coding task.

    Args:
        task: The current task from the Architect's ordered queue.
        manifest: Contents of shared_dependencies.md from disk.

    Returns:
        Generated source code as a string.

    Raises:
        anthropic.APIError: If the Claude API call fails.
    """
```

## Type Annotations
Required on all public function signatures (parameters and return type). Internal helpers should also have them where the type is non-obvious.

## Logging
- Import: `from utils.logger import logger`
- Never use `print()` — use `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`
- Log agent entry/exit at `INFO`; log intermediate steps at `DEBUG`
- Log errors with context: `logger.error("Coder failed task %s: %s", task.name, e)`

## State and File I/O
- **Never store generated code in LangGraph state** — write to `/output/` immediately and store only the file path in state
- State fields hold paths, compact logs, and primitive values — not file contents or LLM transcripts
- Use `pathlib.Path` for all file operations

## Environment Variables
Load via `config.py` only. Never hardcode keys. Never call `os.environ.get()` for required keys — use `os.environ['KEY']` so missing keys fail fast at startup.

## Formatting
Ruff is the formatter and linter. Run `ruff check .` and `ruff format .` before committing. Line length: 100.
