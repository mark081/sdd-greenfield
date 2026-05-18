from flask import Blueprint, render_template

help_bp = Blueprint("help", __name__, url_prefix="/help")


@help_bp.route("", methods=["GET"])
def help_page():
    """GET /help — render the HTML help page."""
    return render_template("help.html"), 200
