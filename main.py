from dotenv import load_dotenv
load_dotenv()  # reads .env before repository.py needs DATABASE_URL

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import repository

app = FastAPI(title="Task API", version="3.0")

repository.init_db()  # creates table + seeds, same first-run rule as A2


class TaskCreate(BaseModel):
    title: str = ""


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.get("/")
def root():
    return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    # a real health check: also confirms the database is reachable
    try:
        repository.stats()
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok", "db": "unreachable"}


@app.get("/tasks")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return repository.list_tasks(done=done, search=search)


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")
    return repository.create_task(payload.title)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty")
    updated = repository.update_task(task_id, title=payload.title, done=payload.done)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    deleted = repository.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return


@app.get("/stats")
def stats():
    return repository.stats()


@app.post("/reset")
def reset():
    repository.reset()
    return {"message": "reset to 3 example tasks"}
