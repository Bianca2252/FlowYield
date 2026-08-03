"""Smoke tests for the FlowYield application foundation."""

import pytest
from app import create_app
from app.extensions import db
from flask import Flask
from flask.testing import FlaskClient


def test_app_uses_testing_configuration(app: Flask) -> None:
    """The fixture should use the isolated testing configuration."""
    assert app.config["TESTING"] is True
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_index_returns_landing_page(
    client: FlaskClient,
) -> None:
    """The main route should display the FlowYield landing page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"FlowYield" in response.data
    assert b"Sign in" in response.data


def test_unknown_configuration_is_rejected() -> None:
    """The factory should reject unsupported configuration names."""
    with pytest.raises(ValueError, match="Unknown configuration: invalid"):
        create_app("invalid")


def test_database_extension_is_initialized(app: Flask) -> None:
    """The SQLAlchemy extension should be bound to the application."""
    assert "sqlalchemy" in app.extensions

    with app.app_context():
        assert db.engine.url.drivername == "sqlite"
        assert str(db.engine.url) == "sqlite:///:memory:"


def test_development_database_uses_instance_directory() -> None:
    """Development should use a local SQLite database."""
    app = create_app("development")

    with app.app_context():
        database_url = str(db.engine.url)

    normalized_database_url = database_url.replace("\\", "/")

    assert normalized_database_url.endswith("/instance/flowyield.db")
