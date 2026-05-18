from flask import Blueprint, render_template

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/contact", methods=["GET"])
def contact_page():
    """GET /contact — render the static HTML contact page."""
    return render_template("contact.html"), 200
