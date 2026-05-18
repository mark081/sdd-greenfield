# Todo App

A simple REST API for managing todo items, built with Flask, Flask-SQLAlchemy, and Pydantic. Follows the application factory pattern and is configured entirely via environment variables.

## Features

- Create, list, retrieve, update, and delete todo items
- Input validation via Pydantic (rejects blank titles, oversized fields, wrong types)
- Persistent storage via SQLAlchemy (SQLite by default, configurable for PostgreSQL)
- Human-readable help page at `GET /help`
- Property-based test suite using Hypothesis

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for package management

## Setup

```bash
# Install dependencies
uv sync
```

## Running Locally

```bash
SECRET_KEY=your-secret-key uv run python -m app.src.run
```

The server binds to `http://127.0.0.1:5001` by default.

To use a custom database:

```bash
SECRET_KEY=your-secret-key DATABASE_URL=sqlite:///instance/todos.db uv run python -m app.src.run
```

## Production (gunicorn)

```bash
SECRET_KEY=your-secret-key gunicorn wsgi:app
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Flask secret key. App refuses to start without it. |
| `DATABASE_URL` | No | `sqlite:///todos.db` | SQLAlchemy database connection string. |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/todos` | Create a new todo item |
| `GET` | `/todos` | List all todo items (ordered by creation time) |
| `GET` | `/todos/<id>` | Retrieve a single todo item |
| `PUT` | `/todos/<id>` | Update a todo item |
| `DELETE` | `/todos/<id>` | Delete a todo item |
| `GET` | `/help` | HTML help page documenting the API |

### Create a Todo

```bash
curl -X POST http://127.0.0.1:5001/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2% fat"}'
```

Response (201):
```json
{
  "id": 1,
  "title": "Buy milk",
  "description": "2% fat",
  "completed": false,
  "created_at": "2024-01-15T10:30:00.000000+00:00Z"
}
```

### List Todos

```bash
curl http://127.0.0.1:5001/todos
```

### Update a Todo

```bash
curl -X PUT http://127.0.0.1:5001/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### Delete a Todo

```bash
curl -X DELETE http://127.0.0.1:5001/todos/1
```

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 204 | Deleted (no body) |
| 400 | Bad request (malformed JSON or invalid path parameter) |
| 404 | Item not found |
| 422 | Validation error (invalid field value or missing required field) |
| 500 | Internal server error |

Error responses always include a `message` field:
```json
{ "message": "title: field required" }
```

## Running Tests

```bash
# All tests
uv run pytest -v

# Property-based tests only
uv run pytest tests/property/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v
```

## Project Structure

```
├── app/
│   └── src/
│       ├── __init__.py        # Application factory (create_app)
│       ├── config.py          # Config classes (Base, Development, Production)
│       ├── extensions.py      # Shared SQLAlchemy instance
│       ├── models/
│       │   └── todo.py        # TodoItem ORM model
│       ├── routes/
│       │   ├── todos.py       # CRUD blueprint (/todos)
│       │   └── help.py        # Help page blueprint (/help)
│       ├── schemas/
│       │   └── todo_schemas.py  # Pydantic validation schemas
│       ├── static/
│       └── templates/
│           └── help.html      # API help page
├── tests/
│   ├── conftest.py            # Shared fixtures (app, client)
│   ├── unit/                  # Schema and model unit tests
│   ├── integration/           # Flask test client integration tests
│   └── property/              # Hypothesis property-based tests
├── wsgi.py                    # Gunicorn entry point
├── main.py
└── pyproject.toml
```
