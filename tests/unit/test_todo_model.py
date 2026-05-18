"""Unit tests for the TodoItem ORM model."""
import os
from datetime import datetime, timezone

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="module")
def flask_app():
    """Minimal Flask app context for ORM model instantiation."""
    from app.src import create_app

    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    from app.src.extensions import db

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


class TestTodoDictSerialization:
    """Tests for TodoItem.to_dict()."""

    def _make_item(self, flask_app, **kwargs):
        from app.src.models.todo import TodoItem

        defaults = {
            "title": "Test todo",
            "description": None,
            "completed": False,
            "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        }
        defaults.update(kwargs)
        with flask_app.app_context():
            item = TodoItem(**defaults)
            return item

    def test_all_five_fields_present(self, flask_app):
        item = self._make_item(flask_app)
        d = item.to_dict()
        assert set(d.keys()) == {"id", "title", "description", "completed", "created_at"}

    def test_created_at_ends_with_z(self, flask_app):
        item = self._make_item(flask_app)
        assert item.to_dict()["created_at"].endswith("Z")

    def test_created_at_is_iso8601(self, flask_app):
        item = self._make_item(flask_app)
        ts = item.to_dict()["created_at"]
        # Should parse as ISO 8601 — strip trailing Z and parse
        datetime.fromisoformat(ts.rstrip("Z"))

    def test_completed_defaults_false(self, flask_app):
        item = self._make_item(flask_app)
        assert item.to_dict()["completed"] is False

    def test_description_none_when_absent(self, flask_app):
        item = self._make_item(flask_app, description=None)
        assert item.to_dict()["description"] is None

    def test_description_present_when_set(self, flask_app):
        item = self._make_item(flask_app, description="Some details")
        assert item.to_dict()["description"] == "Some details"

    def test_title_serialized_correctly(self, flask_app):
        item = self._make_item(flask_app, title="Walk the dog")
        d = item.to_dict()
        assert d["title"] == "Walk the dog"
