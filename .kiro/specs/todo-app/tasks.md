# Implementation Plan: Todo App

## Overview

Implement a Flask-based REST API for managing todo items using the application factory pattern. The implementation proceeds layer-by-layer — project scaffolding, configuration, data model, Pydantic schemas, route handlers, help page, and finally the test suite — so each step integrates cleanly into the previous one.

## Tasks

- [ ] 1. Scaffold project structure and install dependencies
  - Create the directory tree: `app/src/`, `app/src/static/`, `app/src/models/`, `app/src/routes/`, `app/src/schemas/`, `app/src/templates/`, `tests/unit/`, `tests/integration/`, `tests/property/`
  - Initialise the project with `uv init` (if not already done) and add runtime dependencies: `uv add flask flask-sqlalchemy pydantic gunicorn`
  - Add dev/test dependencies: `uv add --dev pytest pytest-flask hypothesis`
  - Create empty `__init__.py` files in every package directory
  - Create `pyproject.toml` `[tool.hatch.build.targets.wheel]` entry pointing to `app/src`
  - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [ ] 2. Implement configuration and application factory
  - [ ] 2.1 Create `app/src/config.py` with `BaseConfig`, `DevelopmentConfig`, and `ProductionConfig` classes
    - `BaseConfig`: `SQLALCHEMY_TRACK_MODIFICATIONS = False`
    - `DevelopmentConfig(BaseConfig)`: `DEBUG = True`
    - `ProductionConfig(BaseConfig)`: `DEBUG = False`
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ] 2.2 Create `app/src/extensions.py` with the shared `SQLAlchemy` instance
    - Single `db = SQLAlchemy()` instance imported by models and the factory
    - _Requirements: 6.1_

  - [ ] 2.3 Create `app/src/__init__.py` with the `create_app()` factory
    - Read `SECRET_KEY` from `os.environ`; raise `RuntimeError` and log an error if absent
    - Read `DATABASE_URL` from `os.environ`; default to `sqlite:///todos.db`
    - Call `db.init_app(app)`, register blueprints (`todos_bp`, `help_bp`), register global error handlers (400, 404, 422, 500)
    - Call `db.create_all()` inside an app context
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 3. Implement the `TodoItem` ORM model
  - [ ] 3.1 Create `app/src/models/todo.py` with the `TodoItem` SQLAlchemy model
    - Columns: `id` (Integer PK autoincrement), `title` (String 200, not null), `description` (Text, nullable), `completed` (Boolean, not null, default `False`), `created_at` (DateTime, not null, default `datetime.utcnow`)
    - Implement `to_dict()` returning all five fields with `created_at` formatted as ISO 8601 UTC (`isoformat() + "Z"`)
    - _Requirements: 1.1, 1.5, 1.6, 2.3, 3.1_

  - [ ]* 3.2 Write unit tests for `TodoItem.to_dict()`
    - Verify all five fields are present in the returned dict
    - Verify `created_at` ends with `"Z"` and is a valid ISO 8601 string
    - Verify `completed` defaults to `False`
    - _Requirements: 1.5, 2.3_

- [ ] 4. Implement Pydantic validation schemas
  - [ ] 4.1 Create `app/src/schemas/todo_schemas.py` with `TodoCreateSchema` and `TodoUpdateSchema`
    - `TodoCreateSchema`: `title` required, `min_length=1`, `max_length=200`, `field_validator` strips and rejects whitespace-only values; `description` optional, `min_length=1`, `max_length=1000`
    - `TodoUpdateSchema`: all fields optional; same `title` validator; `completed` typed as `bool | None`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 1.2, 1.3, 1.4, 4.3, 4.4, 4.5_

  - [ ]* 4.2 Write unit tests for `TodoCreateSchema`
    - Valid title (1 char, 200 chars, mixed whitespace-padded) → accepted and stripped
    - Empty string title → `ValidationError`
    - Whitespace-only title → `ValidationError`
    - Title > 200 chars → `ValidationError`
    - Missing `title` field → `ValidationError`
    - Optional `description` absent → `None`; present with valid length → accepted
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 4.3 Write unit tests for `TodoUpdateSchema`
    - Partial update with only `completed` → accepted
    - Partial update with only `title` → accepted
    - `completed` as non-boolean → `ValidationError`
    - Whitespace-only `title` → `ValidationError`
    - _Requirements: 4.3, 4.4, 4.5_

  - [ ]* 4.4 Write property test for whitespace-only title rejection (Property 2)
    - **Property 2: Whitespace-only titles are always rejected**
    - **Validates: Requirements 1.2, 4.3, 7.2, 7.3**
    - Use `st.text(alphabet=" \t\n\r", min_size=1)` as title; assert `ValidationError` raised for both `TodoCreateSchema` and `TodoUpdateSchema`

  - [ ]* 4.5 Write property test for over-length title rejection (Property 3)
    - **Property 3: Titles exceeding 200 characters are always rejected**
    - **Validates: Requirements 1.3, 4.4, 7.4**
    - Use `st.text(min_size=201)` as title; assert `ValidationError` raised for both schemas

  - [ ]* 4.6 Write property test for missing required field (Property 4)
    - **Property 4: Missing required field always returns 422 with a message**
    - **Validates: Requirements 1.4, 7.5**
    - Construct dicts without `title` key; assert `ValidationError` raised by `TodoCreateSchema`

- [ ] 5. Implement the todos blueprint and CRUD route handlers
  - [ ] 5.1 Create `app/src/routes/todos.py` with the `todos_bp` Blueprint (prefix `/todos`)
    - Implement `POST /todos` (`create_todo`): parse JSON, validate with `TodoCreateSchema`, persist `TodoItem`, return `to_dict()` with HTTP 201
    - Implement `GET /todos` (`list_todos`): query all `TodoItem` rows ordered by `created_at` ascending, return JSON array with HTTP 200
    - Implement `GET /todos/<int:id>` (`get_todo`): fetch by PK, return `to_dict()` with HTTP 200 or `{"message": "Todo item not found"}` with HTTP 404
    - Implement `PUT /todos/<int:id>` (`update_todo`): guard against non-JSON body (HTTP 400), validate with `TodoUpdateSchema`, apply changes, return updated `to_dict()` with HTTP 200 or 404
    - Implement `DELETE /todos/<int:id>` (`delete_todo`): fetch by PK, delete, return HTTP 204; 404 if not found; use string converter with manual int check for non-integer IDs (HTTP 400)
    - Catch `ValidationError` in each handler and return `{"message": "<field>: <reason>"}` with HTTP 422
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3_

  - [ ]* 5.2 Write integration tests for `POST /todos`
    - Valid body → 201 + all five fields in response
    - Missing `title` → 422
    - Whitespace-only `title` → 422
    - `title` > 200 chars → 422
    - With valid `description` → 201 + description persisted
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

  - [ ]* 5.3 Write integration tests for `GET /todos` and `GET /todos/<id>`
    - Empty DB → 200 + `[]`
    - After inserts → 200 + items ordered by `created_at` ascending
    - Existing ID → 200 + correct item shape
    - Non-existent ID → 404 + `message` field
    - Non-integer ID → 404 (Flask converter)
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [ ]* 5.4 Write integration tests for `PUT /todos/<id>` and `DELETE /todos/<id>`
    - Valid update → 200 + updated fields reflected
    - Non-JSON body → 400
    - Non-existent ID → 404
    - Whitespace-only title → 422
    - `completed` non-boolean → 422
    - Delete existing → 204
    - Delete non-existent → 404
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3_

  - [ ]* 5.5 Write property test for creation round-trip (Property 1)
    - **Property 1: Creation round-trip preserves all fields**
    - **Validates: Requirements 1.1, 1.6, 2.3, 3.1**
    - Use `st.text(min_size=1, max_size=200).filter(str.strip)` for title; optional `st.text(min_size=1, max_size=1000)` for description; POST then GET by returned `id`; assert all fields match

  - [ ]* 5.6 Write property test for creation defaults (Property 5)
    - **Property 5: Newly created items have correct default values**
    - **Validates: Requirements 1.5**
    - Random valid payloads; assert `completed == False` and `created_at` matches ISO 8601 UTC pattern

  - [ ]* 5.7 Write property test for list ordering (Property 6)
    - **Property 6: List is always ordered by creation time ascending**
    - **Validates: Requirements 2.1**
    - `st.integers(min_value=1, max_value=10)` for N; create N todos sequentially; assert `GET /todos` returns them sorted by `created_at` ascending

  - [ ]* 5.8 Write property test for update round-trip (Property 7)
    - **Property 7: Update round-trip reflects all changed fields**
    - **Validates: Requirements 4.1, 4.5**
    - Create a todo, then PUT with random valid `title`, `description`, and `completed`; GET and assert all updated fields match

  - [ ]* 5.9 Write property test for delete removes item (Property 8)
    - **Property 8: Delete removes item from all access paths**
    - **Validates: Requirements 5.1, 3.2**
    - Create a todo, DELETE it (assert 204), then assert `GET /todos` has no item with that `id` and `GET /todos/<id>` returns 404

  - [ ]* 5.10 Write property test for non-existent ID returns 404 (Property 9)
    - **Property 9: Non-existent ID always returns 404 with a message field**
    - **Validates: Requirements 3.2, 5.2**
    - `st.integers(min_value=1)` against empty DB; assert both `GET /todos/<id>` and `DELETE /todos/<id>` return 404 with `message` field

- [ ] 6. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement the help blueprint and template
  - [ ] 7.1 Create `app/src/routes/help.py` with the `help_bp` Blueprint (prefix `/help`)
    - Single `GET /help` handler that renders `app/src/templates/help.html` with HTTP 200
    - _Requirements: 8.1, 8.4_

  - [ ] 7.2 Create `app/src/templates/help.html`
    - Document all five API endpoints: `POST /todos`, `GET /todos`, `GET /todos/<id>`, `PUT /todos/<id>`, `DELETE /todos/<id>`
    - For each endpoint: HTTP method, path, accepted request body fields (where applicable), and possible HTTP response codes
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 7.3 Write integration test for `GET /help`
    - Assert HTTP 200 and `Content-Type: text/html`
    - Assert response body contains each of the five endpoint paths
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 8. Wire application entry points
  - [ ] 8.1 Create `app/src/run.py` (development entry point)
    - Call `create_app()` and run with `host="127.0.0.1"`, `port=5001`
    - _Requirements: 6.5_

  - [ ] 8.2 Create `wsgi.py` (production gunicorn entry point)
    - Expose `app = create_app()` for gunicorn to discover
    - _Requirements: 6.5_

  - [ ]* 8.3 Write integration test for missing `SECRET_KEY` at startup
    - Monkeypatch `os.environ` to remove `SECRET_KEY`; assert `create_app()` raises `RuntimeError`
    - _Requirements: 6.3_

- [ ] 9. Final checkpoint — Ensure all tests pass
  - Run `uv run pytest -v` and confirm all tests pass with no warnings. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests (Hypothesis) validate universal correctness properties; unit/integration tests validate specific examples and edge cases
- All property tests use `@settings(max_examples=100)` and include a comment `# Feature: todo-app, Property N: <property text>`
- Run tests with `uv run pytest` or `uv run pytest tests/property/` for property tests only

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "2.2"] },
    { "id": 1, "tasks": ["2.3"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["3.2", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6", "5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "7.1", "7.2"] },
    { "id": 6, "tasks": ["7.3", "8.1", "8.2"] },
    { "id": 7, "tasks": ["8.3"] }
  ]
}
```
