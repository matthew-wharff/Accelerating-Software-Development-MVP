# Code Review: `generated_main.py`

## Critical Issues

### 1. **Import Order Violation** (Lines 1–7)
The imports are not grouped according to project conventions. Standard library and third-party imports are interleaved.

**Current:**
```python
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import sqlite3
from contextlib import contextmanager
```

**Should be:**
```python
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
```

Also: `Depends` is imported on line 5 but never used — remove it.

---

### 2. **No Logging Implementation** (Entire file)
Conventions require `from utils.logger import logger` and all logging via `logger.debug()`, `logger.info()`, etc. This file uses no logging at all.

- Add logger import
- Replace any meaningful execution points with `logger.info()` calls (e.g., startup, task creation)
- Add error logging to `except` blocks (none currently exist)

Example: Line 46 should log `logger.info("Database initialized")`

---

### 3. **Missing Error Handling for Database Operations**
Multiple database operations lack `try/except` blocks:

- **Line 43:** `conn.execute()` in `init_database()` could fail
- **Line 67-68:** INSERT query (line 67-68) could fail due to constraint violations
- **Line 101:** SELECT after INSERT (line 71) could theoretically fail
- **Line 106:** All SELECT queries lack exception handling for corrupted timestamps

**Bug on Line 75:** If `datetime.fromisoformat()` fails due to malformed timestamp in DB, the endpoint crashes with 500 instead of being caught.

Add explicit error handling:
```python
try:
    created_at = datetime.fromisoformat(row['created_at'])
except ValueError as e:
    logger.error("Invalid timestamp in database for task %d: %s", row['id'], e)
    raise HTTPException(status_code=500, detail="Database corruption detected")
```

---

### 4. **Unused Import: `Depends`** (Line 5)
`Depends` from FastAPI is imported but never used. Remove it.

---

## Style Issues

### 5. **Missing Docstring on `get_db()`** (Lines 37–42)
The context manager lacks a Google-style docstring per conventions.

Add:
```python
def get_db():
    """Provide a database connection with row factory enabled.
    
    Yields:
        sqlite3.Connection: Database connection with Row row factory.
    """
```

---

### 6. **Hardcoded Configuration** (Line 10)
`DATABASE_PATH = "tasks.db"` should be loaded from config or environment, not hardcoded. Per conventions: "Never hardcode keys."

Should be:
```python
from config import DATABASE_PATH  # or os.environ['DATABASE_PATH']
```

---

### 7. **Docstring Missing on `init_database()`** (Line 44)
Present but incomplete — should document `Raises`:

```python
def init_database():
    """Initialize the database with the tasks table.
    
    Raises:
        sqlite3.Error: If table creation fails.
    """
```

---

### 8. **Repetitive Task Object Construction**
Lines 70–77, 104–111, 132–139, 159–166 all repeat the same Task construction logic. Extract to a helper function to violate DRY principle:

```python
def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert a database row to a Task object.
    
    Args:
        row: A sqlite3.Row from the tasks table.
    
    Returns:
        Task: The Task object.
    
    Raises:
        ValueError: If row contains invalid timestamp.
    """
    try:
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    except ValueError as e:
        logger.error("Failed to parse task row: %s", e)
        raise
```

---

## Edge Cases & Bugs

### 9. **SQL Injection Risk in `update_task()`** (Line 143)
Line 143 uses f-string interpolation with user-controlled field names:
```python
query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
```

While `update_fields` is constructed from hardcoded strings, this pattern is fragile. However, the current construction is safe because field names come from constants. **Mark as low-risk but note for future developers.**

---

### 10. **Missing Validation: `skip` and `limit` Parameters** (Line 84)
The `get_tasks()` endpoint accepts `skip: int = 0, limit: int = 100` with no bounds checking. A malicious client could request `skip=999999999` or `limit=1000000`.

Add validation:
```python
@app.get("/tasks", response_model=List[Task])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None
):
    """Get all tasks with optional filtering by completion status.
    
    Args:
        skip: Number of tasks to skip (min 0, max 10000).
        limit: Number of tasks to return (min 1, max 1000).
        completed: Filter by completion status.
    
    Returns:
        List of Task objects.
    """
    if skip < 0 or skip > 10000:
        raise HTTPException(status_code=400, detail="skip must be between 0 and 10000")
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    # ... rest of function
```

---

### 11. **Race Condition in `create_task()`** (Lines 67–72)
Between `INSERT` (line 67) and the subsequent `SELECT` (line 71), another request could delete the task. While unlikely, the second query could return `None`. Line 73 checks for this, but there's a logical assumption the task still exists.

The current code is defensive (checks for None), so no bug, but document this assumption.

---

### 12. **Pydantic `regex` Deprecated** (Lines 15, 20)
`regex` parameter in Pydantic v2 is deprecated. Use `pattern` instead:

```python
priority: str = Field("medium", pattern="^(low|medium|high)$", description="Task priority")
```

---

### 13. **Missing Content-Type & 204 Response Body** (Line 168)
The `DELETE` endpoint returns 204 (No Content) correctly, but FastAPI should not return a body. Current code doesn't return anything (implicitly `None`), which is correct, but be explicit:

```python
@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int) -> None:
    """Delete a specific task."""
    # ...
```

---

### 14. **No Transaction Isolation**
SQLite with default isolation level is susceptible to race conditions. Consider:
- Multiple concurrent requests modifying the same task
- No explicit transaction control (each connection auto-commits)

This is acceptable for a simple app but should be documented or improved with explicit transactions:

```python
conn.execute("BEGIN IMMEDIATE")  # Use IMMEDIATE or EXCLUSIVE
```

---

## Missing Features (Not Bugs, But Conventions)

### 15. **No Type Annotations on Database Helper**
`get_db()` should be annotated:
```python
@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    ...
```

Requires: `from typing import Iterator` (add to imports).

---

### 16. **Async Functions with Sync I/O**
All endpoints are `async` but perform blocking I/O (SQLite).