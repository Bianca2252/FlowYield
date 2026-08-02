"""Routes for the main application area."""

from flask import jsonify
from flask_login import current_user, login_required

from app.main import main_bp


@main_bp.get("/")
def index():
    """Return a temporary application status response."""
    return jsonify(
        {
            "application": "FlowYield",
            "status": "running",
        }
    )


@main_bp.get("/dashboard")
@login_required
def dashboard():
    """Return a temporary authenticated dashboard response."""
    return jsonify(
        {
            "application": "FlowYield",
            "user": current_user.email,
            "status": "authenticated",
        }
    )
