import logging
import os

from flask import Flask, jsonify

from app.src.extensions import db

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory — creates and configures the Flask app."""
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        logger.error("SECRET_KEY environment variable is required but not set")
        raise RuntimeError("SECRET_KEY environment variable is required")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///todos.db")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialise extensions
    db.init_app(app)

    # Register blueprints
    from app.src.routes.todos import todos_bp
    from app.src.routes.help import help_bp

    app.register_blueprint(todos_bp)
    app.register_blueprint(help_bp)

    # Register global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"message": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Not found"}), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"message": "Unprocessable entity"}), 422

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error: %s", e)
        return jsonify({"message": "Internal server error"}), 500

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
