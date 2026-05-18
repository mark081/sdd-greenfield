"""Unit tests for Pydantic validation schemas."""
import pytest
from pydantic import ValidationError

from app.src.schemas.todo_schemas import TodoCreateSchema, TodoUpdateSchema


class TestTodoCreateSchema:
    def test_valid_title_accepted(self):
        schema = TodoCreateSchema(title="Buy milk")
        assert schema.title == "Buy milk"

    def test_single_char_title_accepted(self):
        schema = TodoCreateSchema(title="A")
        assert schema.title == "A"

    def test_200_char_title_accepted(self):
        schema = TodoCreateSchema(title="x" * 200)
        assert len(schema.title) == 200

    def test_title_is_stripped(self):
        schema = TodoCreateSchema(title="  Buy milk  ")
        assert schema.title == "Buy milk"

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema(title="")

    def test_whitespace_only_title_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema(title="   ")

    def test_title_over_200_chars_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema(title="x" * 201)

    def test_missing_title_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema()

    def test_description_absent_defaults_to_none(self):
        schema = TodoCreateSchema(title="Test")
        assert schema.description is None

    def test_valid_description_accepted(self):
        schema = TodoCreateSchema(title="Test", description="Some details")
        assert schema.description == "Some details"

    def test_description_over_1000_chars_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema(title="Test", description="x" * 1001)

    def test_description_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            TodoCreateSchema(title="Test", description="")


class TestTodoUpdateSchema:
    def test_partial_update_completed_only(self):
        schema = TodoUpdateSchema(completed=True)
        assert schema.completed is True
        assert schema.title is None

    def test_partial_update_title_only(self):
        schema = TodoUpdateSchema(title="New title")
        assert schema.title == "New title"
        assert schema.completed is None

    def test_all_fields_optional(self):
        schema = TodoUpdateSchema()
        assert schema.title is None
        assert schema.description is None
        assert schema.completed is None

    def test_completed_non_boolean_rejected(self):
        with pytest.raises(ValidationError):
            TodoUpdateSchema(completed="yes")

    def test_whitespace_only_title_rejected(self):
        with pytest.raises(ValidationError):
            TodoUpdateSchema(title="   ")

    def test_title_over_200_chars_rejected(self):
        with pytest.raises(ValidationError):
            TodoUpdateSchema(title="x" * 201)

    def test_title_stripped(self):
        schema = TodoUpdateSchema(title="  hello  ")
        assert schema.title == "hello"
