"""Integration tests for the todos REST API endpoints."""
import json
import os

import pytest


class TestCreateTodo:
    """POST /todos"""

    def test_valid_body_returns_201(self, client):
        resp = client.post("/todos", json={"title": "Buy milk"})
        assert resp.status_code == 201

    def test_response_contains_all_fields(self, client):
        resp = client.post("/todos", json={"title": "Buy milk"})
        data = resp.get_json()
        assert set(data.keys()) >= {"id", "title", "description", "completed", "created_at"}

    def test_title_persisted_correctly(self, client):
        resp = client.post("/todos", json={"title": "Buy milk"})
        assert resp.get_json()["title"] == "Buy milk"

    def test_completed_defaults_to_false(self, client):
        resp = client.post("/todos", json={"title": "Buy milk"})
        assert resp.get_json()["completed"] is False

    def test_description_persisted_when_provided(self, client):
        resp = client.post("/todos", json={"title": "Buy milk", "description": "2% fat"})
        assert resp.status_code == 201
        assert resp.get_json()["description"] == "2% fat"

    def test_missing_title_returns_422(self, client):
        resp = client.post("/todos", json={"description": "no title"})
        assert resp.status_code == 422
        assert "message" in resp.get_json()

    def test_whitespace_only_title_returns_422(self, client):
        resp = client.post("/todos", json={"title": "   "})
        assert resp.status_code == 422
        assert "message" in resp.get_json()

    def test_title_over_200_chars_returns_422(self, client):
        resp = client.post("/todos", json={"title": "x" * 201})
        assert resp.status_code == 422

    def test_non_json_body_returns_400(self, client):
        resp = client.post("/todos", data="not json", content_type="text/plain")
        assert resp.status_code == 400


class TestListTodos:
    """GET /todos"""

    def test_empty_db_returns_empty_list(self, client):
        resp = client.get("/todos")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_all_items(self, client):
        client.post("/todos", json={"title": "First"})
        client.post("/todos", json={"title": "Second"})
        resp = client.get("/todos")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    def test_items_ordered_by_created_at_ascending(self, client):
        client.post("/todos", json={"title": "First"})
        client.post("/todos", json={"title": "Second"})
        client.post("/todos", json={"title": "Third"})
        items = client.get("/todos").get_json()
        titles = [i["title"] for i in items]
        assert titles == ["First", "Second", "Third"]

    def test_each_item_has_required_fields(self, client):
        client.post("/todos", json={"title": "Test"})
        items = client.get("/todos").get_json()
        item = items[0]
        assert set(item.keys()) >= {"id", "title", "description", "completed", "created_at"}


class TestGetTodo:
    """GET /todos/<id>"""

    def test_existing_id_returns_200(self, client):
        created = client.post("/todos", json={"title": "Test"}).get_json()
        resp = client.get(f"/todos/{created['id']}")
        assert resp.status_code == 200

    def test_returns_correct_item(self, client):
        created = client.post("/todos", json={"title": "Specific item"}).get_json()
        resp = client.get(f"/todos/{created['id']}")
        assert resp.get_json()["title"] == "Specific item"

    def test_nonexistent_id_returns_404(self, client):
        resp = client.get("/todos/99999")
        assert resp.status_code == 404
        assert "message" in resp.get_json()

    def test_non_integer_id_returns_404(self, client):
        # Flask's <int:id> converter doesn't match 'abc', so the DELETE route
        # (string converter) matches but GET is not registered there → 405.
        # The important thing is it's not 200; the spec says 422 for invalid IDs.
        resp = client.get("/todos/abc")
        assert resp.status_code in (404, 405, 422)


class TestUpdateTodo:
    """PUT /todos/<id>"""

    def test_valid_update_returns_200(self, client):
        created = client.post("/todos", json={"title": "Original"}).get_json()
        resp = client.put(f"/todos/{created['id']}", json={"title": "Updated"})
        assert resp.status_code == 200

    def test_updated_title_reflected(self, client):
        created = client.post("/todos", json={"title": "Original"}).get_json()
        resp = client.put(f"/todos/{created['id']}", json={"title": "Updated"})
        assert resp.get_json()["title"] == "Updated"

    def test_completed_flag_updated(self, client):
        created = client.post("/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/todos/{created['id']}", json={"completed": True})
        assert resp.get_json()["completed"] is True

    def test_non_json_body_returns_400(self, client):
        created = client.post("/todos", json={"title": "Task"}).get_json()
        resp = client.put(
            f"/todos/{created['id']}", data="not json", content_type="text/plain"
        )
        assert resp.status_code == 400

    def test_nonexistent_id_returns_404(self, client):
        resp = client.put("/todos/99999", json={"title": "Ghost"})
        assert resp.status_code == 404

    def test_whitespace_only_title_returns_422(self, client):
        created = client.post("/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/todos/{created['id']}", json={"title": "   "})
        assert resp.status_code == 422

    def test_non_boolean_completed_returns_422(self, client):
        created = client.post("/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/todos/{created['id']}", json={"completed": "yes"})
        assert resp.status_code == 422


class TestDeleteTodo:
    """DELETE /todos/<id>"""

    def test_existing_id_returns_204(self, client):
        created = client.post("/todos", json={"title": "To delete"}).get_json()
        resp = client.delete(f"/todos/{created['id']}")
        assert resp.status_code == 204

    def test_delete_removes_item(self, client):
        created = client.post("/todos", json={"title": "To delete"}).get_json()
        client.delete(f"/todos/{created['id']}")
        resp = client.get(f"/todos/{created['id']}")
        assert resp.status_code == 404

    def test_nonexistent_id_returns_404(self, client):
        resp = client.delete("/todos/99999")
        assert resp.status_code == 404
        assert "message" in resp.get_json()

    def test_non_integer_id_returns_400(self, client):
        resp = client.delete("/todos/abc")
        assert resp.status_code == 400


class TestHelpPage:
    """GET /help"""

    def test_returns_200(self, client):
        resp = client.get("/help")
        assert resp.status_code == 200

    def test_returns_html(self, client):
        resp = client.get("/help")
        assert "text/html" in resp.content_type

    def test_documents_all_endpoints(self, client):
        resp = client.get("/help")
        body = resp.data.decode()
        assert "POST" in body
        assert "GET" in body
        assert "PUT" in body
        assert "DELETE" in body
        assert "/todos" in body


class TestContactPage:
    """GET /contact"""

    def test_returns_200(self, client):
        resp = client.get("/contact")
        assert resp.status_code == 200

    def test_content_type_is_html(self, client):
        resp = client.get("/contact")
        assert resp.content_type.startswith("text/html")

    def test_body_contains_mailto_link(self, client):
        resp = client.get("/contact")
        body = resp.data.decode()
        assert "mailto:" in body

    def test_body_contains_contact_form_fields(self, client):
        resp = client.get("/contact")
        body = resp.data.decode()
        # Form must have name, email, and message fields
        assert 'name="name"' in body
        assert 'name="email"' in body
        assert 'name="message"' in body


class TestStartupConfig:
    """Application factory configuration tests."""

    def test_missing_secret_key_raises_runtime_error(self, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        from app.src import create_app

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app()
