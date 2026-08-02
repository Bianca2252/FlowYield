"""Application error handlers."""

from flask import Flask, jsonify


def register_error_handlers(app: Flask) -> None:
    """Register application-wide HTTP error handlers."""

    @app.errorhandler(403)
    def forbidden(_error):
        """Return a consistent forbidden response."""
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "message": "You do not have permission to access this resource.",
                }
            ),
            403,
        )
