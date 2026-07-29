import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Task API", version="2.0")

DB_FILE = "tasks.db"


def get_db():
    # check_same_thread=False is fine here: FastAPI's dev server is single-process
    # and each request opens its own short-lived connection.
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, like a dict
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    # seed only if the table is empty, so restarts never duplicate the examples
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy groceries", 0)
        )
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", ("Finish CRUD assignment", 0)
        )
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", ("Read about REST", 1)
        )
        conn.commit()
    conn.close()


init_db()  # runs once when the app starts


# ---- Request body models ----
class TaskCreate(BaseModel):
    title: str = ""  # default empty so a missing title reaches OUR 400 check


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# ---- Stage: root and health ----
@app.get("/")
def root():
    return {"name": "Task API", "version": "2.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Stage 1: Read from the database ----
# Stage 1 confirmed working: tested GET /tasks and GET /tasks/{id} against tasks.db
@app.get("/tasks")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)
    if search is not None:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY title"  # stretch: alphabetical sort
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_dict(row)


# ---- Stage 2: Create — INSERT into the database ----
@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)", (payload.title, 0)
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


# ---- Stage 3: Update & Delete — UPDATE / DELETE with SQL ----
@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    new_title = row["title"]
    if payload.title is not None:
        if not payload.title.strip():
            conn.close()
            raise HTTPException(status_code=400, detail="title cannot be empty")
        new_title = payload.title

    new_done = row["done"]
    if payload.done is not None:
        new_done = 1 if payload.done else 0

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_dict(updated)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return


# ---- Stretch: stats endpoint, computed in SQL ----
@app.get("/stats")
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    conn.close()
    return {"total": total, "done": done_count, "open": total - done_count}


# ---- Stretch: reset ----
@app.post("/reset")
def reset():
    conn = get_db()
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()
    init_db()  # re-seeds since the table is now empty
    return {"message": "reset to 3 example tasks"}
