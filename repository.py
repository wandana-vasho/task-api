"""
repository.py

Every line that talks to the database lives here, and only here.
main.py (the routes) never sees SQL directly - it just calls these
functions. This is the "repository" pattern the assignment asks for:
swapping storage (memory -> SQLite -> Postgres) should only ever
touch this file.
"""

import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]  # fails loudly if .env wasn't loaded


def get_conn():
    # dict_row lets us access columns by name, e.g. row["title"]
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        if count == 0:
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Buy groceries", False)
            )
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Finish CRUD assignment", False)
            )
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Read about REST", True)
            )
        conn.commit()


def list_tasks(done=None, search=None):
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if done is not None:
        query += " AND done = %s"
        params.append(done)
    if search is not None:
        query += " AND title LIKE %s"
        params.append(f"%{search}%")
    query += " ORDER BY title"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


def get_task(task_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()


def create_task(title: str):
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
            (title, False),
        ).fetchone()
        conn.commit()
    return row


def update_task(task_id: int, title=None, done=None):
    existing = get_task(task_id)
    if existing is None:
        return None

    new_title = existing["title"] if title is None else title
    new_done = existing["done"] if done is None else done

    with get_conn() as conn:
        row = conn.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
            (new_title, new_done, task_id),
        ).fetchone()
        conn.commit()
    return row


def delete_task(task_id: int) -> bool:
    existing = get_task(task_id)
    if existing is None:
        return False
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
    return True


def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        done_count = conn.execute(
            "SELECT COUNT(*) AS c FROM tasks WHERE done = TRUE"
        ).fetchone()["c"]
    return {"total": total, "done": done_count, "open": total - done_count}


def reset():
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks")
        conn.commit()
    init_db()
