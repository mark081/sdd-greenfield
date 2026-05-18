"""Shared pytest fixtures for the todo-app test suite."""
import os

import pytest

# Ensure SECRET_KEY is set before importing the app factory
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture()
def app():
    """Create a Flask app configured for testing with an in-memory SQLite DB."""
    from app.src import create_app

    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Re-create tables for the in-memory DB
    from app.src.extensions import db

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()
