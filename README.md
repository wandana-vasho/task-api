# Task API — CRUD Assignment (Backend AI Engineering, Week 2)

A small REST API for managing a to-do list, built with **Python + FastAPI**. Supports full CRUD (Create, Read, Update, Delete) on an in-memory task list, with interactive documentation via Swagger UI.

## What this is

- **CRUD** operations on tasks: create, list, read one, update, delete
- **In-memory storage** — no database yet (data resets when the server restarts, by design — see "The mortality experiment" below)
- **Validation** — the server rejects a task with a missing/empty title
- **Swagger UI** built in at `/docs` for interactive testing

## How to install & run

```bash
# 1. Install dependencies
pip install fastapi uvicorn

# 2. Run the server
python3 -m uvicorn main:app --reload
```

The server starts on **http://localhost:8000**. Open **http://localhost:8000/docs** in your browser for the interactive Swagger UI.

## Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/` | API info | 200 | — |
| GET | `/health` | Health check | 200 | — |
| GET | `/tasks` | List all tasks (supports `?done=true` and `?search=word`) | 200 | — |
| GET | `/tasks/{id}` | Get one task | 200 | 404 if not found |
| POST | `/tasks` | Create a task (`{"title": "..."}`) | 201 | 400 if title missing/empty |
| PUT | `/tasks/{id}` | Update a task's title and/or done status | 200 | 404 if not found, 400 if title is empty |
| DELETE | `/tasks/{id}` | Delete a task | 204 | 404 if not found |
| GET | `/stats` | Task counts (`total`, `done`, `open`) | 200 | — |
| POST | `/reset` | Reset to the 3 example tasks | 200 | — |

## Example: creating a task

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

Response:
```
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

Posting an empty body correctly returns `400`:
```bash
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{}'
# HTTP/1.1 400 Bad Request
# {"detail":"title is required and cannot be empty"}
```

## Swagger UI

Open `/docs` in your browser after starting the server to try every endpoint interactively.

*(Screenshot: add your own — open http://localhost:8000/docs in your browser, take a screenshot, and drop it in this repo as `swagger_screenshot.png`.)*

## Extras I added (stretch goals)

- **Filtering**: `GET /tasks?done=true` returns only completed tasks
- **Search**: `GET /tasks?search=milk` returns tasks whose title contains the word
- **Stats endpoint**: `GET /stats` → `{"total": 3, "done": 1, "open": 2}`
- **Seed & reset**: `POST /reset` restores the 3 example tasks

## A bug I caught while testing

FastAPI's automatic request validation returns its own `422 Unprocessable Entity` when a required Pydantic field is missing — before my own code ever runs. The assignment specifically asks for `400 Bad Request` on an invalid POST body, so I changed the `title` field to default to an empty string in the model, letting my own validation check (`if not title.strip()`) catch it and return the correct `400` instead. Tested both cases directly with curl before and after the fix.

## The mortality experiment

If you create a task, then restart the server, the task is gone — `tasks` lives only in a Python list in memory, not on disk. This is expected: in-memory storage never survives a restart. That's exactly the gap a real database (coming next week) is built to close.

## Tech

Python 3, FastAPI, Uvicorn — no database, no external dependencies beyond the framework itself.
