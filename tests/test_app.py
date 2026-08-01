"""Smoke tests for the FlowYield application foundation."""

import pytest
from app import create_app
from flask import Flask
from flask.testing import FlaskClient


def test_app_uses_testing_configuration(app: Flask) -> None:
    """The fixture should use the isolated testing configuration."""
    assert app.config["TESTING"] is True
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_index_returns_application_status(client: FlaskClient) -> None:
    """The main route should confirm that FlowYield is running."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "FlowYield",
        "status": "running",
    }


def test_unknown_configuration_is_rejected() -> None:
    """The factory should reject unsupported configuration names."""
    with pytest.raises(ValueError, match="Unknown configuration: invalid"):
        create_app("invalid")
