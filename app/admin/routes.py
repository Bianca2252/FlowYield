"""Administration routes."""

from flask import jsonify
from flask_login import current_user

from app.admin import admin_bp
from app.authorization import RoleName, roles_required


@admin_bp.get("/")
@roles_required(RoleName.ADMINISTRATOR)
def index():
    """Return a temporary administration status response."""
    return jsonify(
        {
            "area": "administration",
            "status": "authorized",
            "user": current_user.email,
        }
    )
