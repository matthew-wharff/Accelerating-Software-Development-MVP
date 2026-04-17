from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="Task Manager API", description="A simple task manager with CRUD operations")

DATABASE_PATH = "tasks.db"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    priority: str = Field("medium", regex="^(low|medium|high)$", description="Task priority")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    priority: Optional[str] = Field(None, regex="^(low|medium|high)$", description="Task priority")
    completed: Optional[bool] = Field(None, description="Task completion status")


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    completed: bool
    created_at: datetime
    updated_at: datetime


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize the database with the tasks table."""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


@app.on_event("startup")
async def startup_event():
    init_database()


@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task."""
    with get_db() as conn:
        cursor = conn.execute(
            '''INSERT INTO tasks (title, description, priority) 
               VALUES (?, ?, ?)''',
            (task.title, task.description, task.priority)
        )
        conn.commit()
        task_id = cursor.lastrowid
        
        row = conn.execute(
            'SELECT * FROM tasks WHERE id = ?', (task_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create task")
            
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


@app.get("/tasks", response_model=List[Task])
async def get_tasks(skip: int = 0, limit: int = 100, completed: Optional[bool] = None):
    """Get all tasks with optional filtering by completion status."""
    with get_db() as conn:
        query = 'SELECT * FROM tasks'
        params = []
        
        if completed is not None:
            query += ' WHERE completed = ?'
            params.append(int(completed))
            
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, skip])
        
        rows = conn.execute(query, params).fetchall()
        
        return [
            Task(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                priority=row['priority'],
                completed=bool(row['completed']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
            for row in rows
        ]


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a specific task by ID."""
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM tasks WHERE id = ?', (task_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskUpdate):
    """Update a specific task."""
    with get_db() as conn:
        # Check if task exists
        existing = conn.execute(
            'SELECT * FROM tasks WHERE id = ?', (task_id,)
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if task_update.title is not None:
            update_fields.append('title = ?')
            params.append(task_update.title)
            
        if task_update.description is not None:
            update_fields.append('description = ?')
            params.append(task_update.description)
            
        if task_update.priority is not None:
            update_fields.append('priority = ?')
            params.append(task_update.priority)
            
        if task_update.completed is not None:
            update_fields.append('completed = ?')
            params.append(int(task_update.completed))
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        
        # Return updated task
        row = conn.execute(
            'SELECT * FROM tasks WHERE id = ?', (task_id,)
        ).fetchone()
        
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a specific task."""
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM tasks WHERE id = ?', (task_id,)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Task Manager API",
        "version": "1.0.0",
        "endpoints": {
            "create_task": "POST /tasks",
            "get_tasks": "GET /tasks",
            "get_task": "GET /tasks/{task_id}",
            "update_task": "PUT /tasks/{task_id}",
            "delete_task": "DELETE /tasks/{task_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)