"""Approval task Blueprint."""

from flask import Blueprint

approvals_bp = Blueprint(
    "approvals",
    __name__,
    url_prefix="/approvals",
)


from app.approvals import routes  # noqa: E402, F401
