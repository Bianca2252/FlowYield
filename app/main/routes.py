"""Routes for the main application area."""

from flask import jsonify

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