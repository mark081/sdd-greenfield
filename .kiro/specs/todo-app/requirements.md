# Requirements Document

## Introduction

A simple web-based todo application that allows users to create, view, update, and delete tasks they need to complete. The application is built with Flask using the application factory pattern, persists data via Flask-SQLAlchemy, and validates input with Pydantic. It runs locally on 127.0.0.1:5001 and is configurable via environment variables.

## Glossary

- **Todo_App**: The Flask web application that manages todo items.
- **Todo_Item**: A single task record consisting of a title, optional description, completion status, and timestamps.
- **Todo_List**: The collection of all Todo_Items stored in the database.
- **API**: The HTTP interface exposed by the Todo_App for creating, reading, updating, and deleting Todo_Items.
- **Validator**: The Pydantic-based component responsible for validating request payloads.
- **Database**: The SQLAlchemy-managed persistence layer storing Todo_Items.

---

## Requirements

### Requirement 1: Create a Todo Item

**User Story:** As a user, I want to create a new todo item with a title and optional description, so that I can track things I need to do.

#### Acceptance Criteria

1. WHEN a POST request is received at `/todos` with a valid JSON body containing a `title` field between 1 and 200 characters (non-whitespace), THE Todo_App SHALL persist a new Todo_Item to the Database and return the created item — including its `id`, `title`, `description`, `completed`, and `created_at` fields — with HTTP 201.
2. IF a POST request is received at `/todos` with a `title` field that is an empty string or contains only whitespace, THEN THE Todo_App SHALL return an error response indicating the title is invalid with HTTP 422.
3. IF a POST request is received at `/todos` with a `title` field exceeding 200 characters, THEN THE Todo_App SHALL return an error response indicating the title is too long with HTTP 422.
4. IF a POST request is received at `/todos` with a missing `title` field, THEN THE Todo_App SHALL return an error response indicating the title is required with HTTP 422.
5. THE Todo_Item SHALL be created with `completed` set to `false` and a `created_at` timestamp set to the current UTC time.
6. WHERE a `description` field of between 1 and 1000 characters is included in the request body, THE Todo_App SHALL persist the description alongside the Todo_Item.

---

### Requirement 2: List All Todo Items

**User Story:** As a user, I want to view all my todo items, so that I can see everything I need to do.

#### Acceptance Criteria

1. WHEN a GET request is received at `/todos`, THE Todo_App SHALL return the full Todo_List as a JSON array with HTTP 200, ordered by `created_at` ascending.
2. WHILE the Database contains no Todo_Items, THE Todo_App SHALL return an empty JSON array (`[]`) with HTTP 200.
3. THE Todo_App SHALL return each Todo_Item in the list with its `id` (integer), `title` (string), `description` (string or null), `completed` (boolean), and `created_at` (ISO 8601 UTC timestamp) fields.
4. IF the Database is unavailable when a GET request is received at `/todos`, THEN THE Todo_App SHALL return an error response with HTTP 500.

---

### Requirement 3: Retrieve a Single Todo Item

**User Story:** As a user, I want to retrieve a specific todo item by its ID, so that I can view its details.

#### Acceptance Criteria

1. WHEN a GET request is received at `/todos/<id>` where `<id>` is a positive integer matching an existing Todo_Item, THE Todo_App SHALL return the matching Todo_Item as JSON with HTTP 200, including its `id`, `title`, `description`, `completed`, and `created_at` fields.
2. IF a GET request is received at `/todos/<id>` with an integer ID that does not exist in the Database, THEN THE Todo_App SHALL return a JSON error response with a `message` field indicating the item was not found with HTTP 404.
3. IF a GET request is received at `/todos/<id>` where `<id>` is not a valid positive integer, THEN THE Todo_App SHALL return an error response with HTTP 422.

---

### Requirement 4: Update a Todo Item

**User Story:** As a user, I want to update the title, description, or completion status of a todo item, so that I can keep my list accurate.

#### Acceptance Criteria

1. WHEN a PUT request is received at `/todos/<id>` with a valid JSON body and an existing integer ID, THE Todo_App SHALL update the matching Todo_Item in the Database and return the updated item with HTTP 200.
2. IF a PUT request is received at `/todos/<id>` with an ID that does not exist in the Database, THEN THE Todo_App SHALL return an error response with HTTP 404.
3. IF a PUT request is received at `/todos/<id>` with a `title` field that is an empty string or contains only whitespace, THEN THE Todo_App SHALL return an error response with HTTP 422.
4. IF a PUT request is received at `/todos/<id>` with a `title` field exceeding 200 characters, THEN THE Todo_App SHALL return an error response with HTTP 422.
5. WHERE a `completed` field is included in the request body, THE Todo_App SHALL update the `completed` status of the Todo_Item to the provided boolean value; IF the `completed` field is not a boolean, THEN THE Todo_App SHALL return an error response with HTTP 422.
6. IF a PUT request is received at `/todos/<id>` with a body that is not valid JSON or is empty, THEN THE Todo_App SHALL return an error response with HTTP 400.

---

### Requirement 5: Delete a Todo Item

**User Story:** As a user, I want to delete a todo item, so that I can remove tasks I no longer need to track.

#### Acceptance Criteria

1. WHEN a DELETE request is received at `/todos/<id>` with an existing integer ID, THE Todo_App SHALL remove the matching Todo_Item from the Database and return HTTP 204 with no body.
2. IF a DELETE request is received at `/todos/<id>` with an integer ID that does not exist in the Database, THEN THE Todo_App SHALL return a JSON error response with a `message` field indicating the item was not found with HTTP 404.
3. IF a DELETE request is received at `/todos/<id>` where `<id>` is not a valid positive integer, THEN THE Todo_App SHALL return an error response with HTTP 400.

---

### Requirement 6: Configuration via Environment Variables

**User Story:** As a developer, I want the application to be configured through environment variables, so that I can run it in different environments without changing code.

#### Acceptance Criteria

1. WHEN the Todo_App starts, THE Todo_App SHALL read the database connection string from the `DATABASE_URL` environment variable and use it to configure the Database connection.
2. WHEN the Todo_App starts, THE Todo_App SHALL read the Flask secret key from the `SECRET_KEY` environment variable and use it to configure the application.
3. IF the `SECRET_KEY` environment variable is not set at startup, THEN THE Todo_App SHALL refuse to start and log an error indicating the missing configuration.
4. IF the `DATABASE_URL` environment variable is not set at startup, THEN THE Todo_App SHALL use a default SQLite database path of `sqlite:///todos.db`, resolved relative to the application's working directory.
5. IF the application is started in the local development configuration, THEN THE Todo_App SHALL bind to host `127.0.0.1` and port `5001`.

---

### Requirement 7: Input Validation

**User Story:** As a developer, I want all incoming request data to be validated with Pydantic, so that invalid data never reaches the database layer.

#### Acceptance Criteria

1. WHEN a create or update request is received, THE Validator SHALL validate the request payload before THE Todo_App processes it.
2. WHEN the Validator detects an invalid payload, THE Todo_App SHALL return a JSON error response containing a `message` field that identifies the invalid field and the reason for rejection with HTTP 422.
3. THE Todo_Item `title` field SHALL accept a minimum of 1 and a maximum of 200 non-whitespace characters.
4. IF a `title` value exceeding 200 characters is submitted, THEN THE Validator SHALL reject the request and THE Todo_App SHALL return an error response with HTTP 422.
5. IF a required field is absent from the request payload, THEN THE Validator SHALL reject the request and THE Todo_App SHALL return a JSON error response identifying the missing field with HTTP 422.

---

### Requirement 8: Help Page

**User Story:** As a user, I want to view a help page that explains how to use the todo application, so that I can understand the available features and how to interact with them.

#### Acceptance Criteria

1. WHEN a GET request is received at `/help`, THE Todo_App SHALL return an HTML help page with HTTP 200.
2. THE help page SHALL document each of the five API endpoints — `POST /todos`, `GET /todos`, `GET /todos/<id>`, `PUT /todos/<id>`, and `DELETE /todos/<id>` — including the HTTP method and path for each.
3. THE help page SHALL document, for each endpoint, the accepted request body fields (where applicable) and the possible HTTP response codes.
4. IF an unexpected server error occurs when serving the `/help` route, THEN THE Todo_App SHALL return an error response with HTTP 500.


