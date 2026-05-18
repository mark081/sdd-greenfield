from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.src.extensions import db
from app.src.models.todo import TodoItem
from app.src.schemas.todo_schemas import TodoCreateSchema, TodoUpdateSchema

todos_bp = Blueprint("todos", __name__, url_prefix="/todos")


def _validation_error_message(exc: ValidationError) -> str:
    """Extract the first validation error as 'field: reason'."""
    error = exc.errors()[0]
    field = error["loc"][0] if error["loc"] else "unknown"
    reason = error["msg"]
    return f"{field}: {reason}"


@todos_bp.route("", methods=["POST"])
def create_todo():
    """POST /todos — create a new todo item."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    try:
        schema = TodoCreateSchema(**data)
    except ValidationError as exc:
        return jsonify({"message": _validation_error_message(exc)}), 422

    item = TodoItem(
        title=schema.title,
        description=schema.description,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201


@todos_bp.route("", methods=["GET"])
def list_todos():
    """GET /todos — return all todo items ordered by created_at ascending."""
    items = TodoItem.query.order_by(TodoItem.created_at.asc()).all()
    return jsonify([item.to_dict() for item in items]), 200


@todos_bp.route("/<int:id>", methods=["GET"])
def get_todo(id: int):
    """GET /todos/<id> — return a single todo item by primary key."""
    item = db.session.get(TodoItem, id)
    if item is None:
        return jsonify({"message": "Todo item not found"}), 404

    return jsonify(item.to_dict()), 200


@todos_bp.route("/<int:id>", methods=["PUT"])
def update_todo(id: int):
    """PUT /todos/<id> — update an existing todo item."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    item = db.session.get(TodoItem, id)
    if item is None:
        return jsonify({"message": "Todo item not found"}), 404

    try:
        schema = TodoUpdateSchema(**data)
    except ValidationError as exc:
        return jsonify({"message": _validation_error_message(exc)}), 422

    if schema.title is not None:
        item.title = schema.title
    if schema.description is not None:
        item.description = schema.description
    if schema.completed is not None:
        item.completed = schema.completed

    db.session.commit()

    return jsonify(item.to_dict()), 200


@todos_bp.route("/<id>", methods=["DELETE"])
def delete_todo(id: str):
    """DELETE /todos/<id> — delete a todo item.

    Uses a string converter with manual int check so that non-integer IDs
    return HTTP 400 (rather than the 404 Flask's <int:id> converter would give).
    """
    try:
        todo_id = int(id)
    except (ValueError, TypeError):
        return jsonify({"message": "Todo ID must be a valid integer"}), 400

    item = db.session.get(TodoItem, todo_id)
    if item is None:
        return jsonify({"message": "Todo item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return "", 204
