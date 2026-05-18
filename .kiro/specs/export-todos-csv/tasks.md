# Implementation Plan: Export Todos as CSV

## Overview

Implement a CSV export endpoint for the todo API that returns all (or filtered) todo items as an RFC 4180-compliant CSV file. The implementation adds a new export blueprint, a CSV generation service, and comprehensive tests using Hypothesis for property-based testing and pytest for unit/integration tests.

## Tasks

- [ ] 1. Create the CSV export service
  - [ ] 1.1 Create `app/src/services/__init__.py` and `app/src/services/csv_export.py`
    - Create the `services` directory with an `__init__.py`
    - Implement `CsvExportService` class with a static `generate(items: list[TodoItem]) -> str` method
    - Use Python's `csv` module with `csv.QUOTE_MINIMAL` and `io.StringIO`
    - Write header row with columns: id, title, description, completed, created_at
    - Format fields: id as string, description as empty string for None, completed as lowercase "true"/"false", created_at as ISO 8601 with "Z" suffix
    - Ensure CRLF line endings and UTF-8 encoding without BOM
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.8, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.2, 3.3_

  - [ ]* 1.2 Write property test for CSV round-trip integrity
    - **Property 1: CSV round-trip integrity**
    - Generate random TodoItem instances with arbitrary titles, descriptions (including None), completed states, and created_at timestamps
    - Export via `CsvExportService.generate`, parse with `csv.reader`, verify each field matches original data
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 3.1, 1.1, 1.3, 2.4, 2.5, 2.6**

  - [ ]* 1.3 Write property test for RFC 4180 special character quoting
    - **Property 2: RFC 4180 special character quoting**
    - Generate TodoItems with titles/descriptions containing commas, double quotes, and newline characters
    - Verify the CSV output properly quotes and escapes these fields so a compliant parser recovers original values
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 1.6, 2.1, 2.2, 2.3**

  - [ ]* 1.4 Write unit tests for CsvExportService
    - Test empty list returns header-only CSV with CRLF ending
    - Test specific formatting examples (known input → known output)
    - Test None description produces empty field
    - Test CRLF line endings throughout
    - _Requirements: 1.7, 2.4, 3.3, 4.1_

- [ ] 2. Create the export route and register blueprint
  - [ ] 2.1 Create `app/src/routes/export.py` with the export blueprint
    - Define `export_bp` Blueprint with `url_prefix="/todos"`
    - Implement `GET /export` route handler
    - Parse and validate optional `completed` query parameter (must be exactly "true", "false", or absent)
    - Return 400 JSON error for invalid `completed` values
    - Query `TodoItem` from database with optional filter, ordered by `created_at` ascending
    - Call `CsvExportService.generate` to produce CSV content
    - Return response with `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename=todos.csv`
    - Wrap logic in try/except: catch `SQLAlchemyError` for DB errors (500), general `Exception` for unexpected errors (500)
    - Never return partial CSV on error; always return JSON error response
    - _Requirements: 1.1, 1.4, 1.5, 1.7, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3_

  - [ ] 2.2 Register the export blueprint in `app/src/__init__.py`
    - Import `export_bp` from `app.src.routes.export`
    - Register with `app.register_blueprint(export_bp)`
    - _Requirements: 1.1_

  - [ ]* 2.3 Write property test for completion filter correctness
    - **Property 3: Completion filter correctness**
    - Generate sets of TodoItems with mixed completion states
    - Export with `?completed=true` and verify only completed items returned, ordered by created_at ascending
    - Export with `?completed=false` and verify only incomplete items returned, ordered by created_at ascending
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

  - [ ]* 2.4 Write property test for invalid filter parameter rejection
    - **Property 4: Invalid filter parameter rejection**
    - Generate arbitrary strings that are not exactly "true" or "false"
    - Call the export endpoint with the generated value as `completed` parameter
    - Verify HTTP 400 response with JSON body containing "message" field
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 5.4**

  - [ ]* 2.5 Write unit tests for the export route
    - Test successful export with multiple todos returns correct headers and CSV body
    - Test empty database returns header-only CSV with 200 status
    - Test `?completed=true` filters correctly
    - Test `?completed=false` filters correctly
    - Test absent `completed` parameter returns all items
    - Test invalid `completed` values ("True", "1", "", "yes") return 400 with JSON message
    - _Requirements: 1.4, 1.5, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Integration tests and error handling verification
  - [ ]* 4.1 Write integration tests for error scenarios
    - Test database unavailable scenario returns 500 with JSON `{"message": "Unable to reach data source"}`
    - Test unexpected exception during CSV generation returns 500 with JSON error, no partial CSV
    - Use mocking to simulate database and service failures
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The project uses `uv run pytest` to execute tests
- Property tests use Hypothesis with `@settings(max_examples=100)`
- Test files go in `tests/property/` for property tests, `tests/unit/` for unit tests, and `tests/integration/` for integration tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4", "2.5"] },
    { "id": 4, "tasks": ["4.1"] }
  ]
}
```
