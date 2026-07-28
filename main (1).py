from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Task API", version="1.0")

# ---- In-memory "database" ----
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish CRUD assignment", "done": False},
    {"id": 3, "title": "Read about REST", "done": True},
]
next_id = 4  # tracks the next free id to hand out


# ---- Request body models (used for validation) ----
class TaskCreate(BaseModel):
    title: str = ""  # default empty so a missing title reaches OUR 400 check
                      # instead of FastAPI's automatic 422


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---- Stage 1: root and health ----
@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Stage 2: Read ----
# Stage 2 confirmed working: tested GET /tasks and GET /tasks/{id} with curl
@app.get("/tasks")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    result = tasks
    # stretch: filtering by done
    if done is not None:
        result = [t for t in result if t["done"] == done]
    # stretch: search by title substring
    if search is not None:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---- Stage 3: Create ----
# Stage 3 confirmed working: tested POST /tasks with curl, verified 400 on empty title
@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    global next_id
    new_task = {"id": next_id, "title": payload.title, "done": False}
    tasks.append(new_task)
    next_id += 1
    return new_task


# ---- Stage 4: Update & Delete ----
@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    for t in tasks:
        if t["id"] == task_id:
            if payload.title is not None:
                if not payload.title.strip():
                    raise HTTPException(status_code=400, detail="title cannot be empty")
                t["title"] = payload.title
            if payload.done is not None:
                t["done"] = payload.done
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---- Stretch: stats endpoint ----
@app.get("/stats")
def stats():
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    return {"total": total, "done": done_count, "open": total - done_count}


# ---- Stretch: seed & reset ----
@app.post("/reset")
def reset():
    global tasks, next_id
    tasks = [
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Finish CRUD assignment", "done": False},
        {"id": 3, "title": "Read about REST", "done": True},
    ]
    next_id = 4
    return {"message": "reset to 3 example tasks"}
