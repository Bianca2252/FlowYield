"""Shared pytest fixtures for FlowYield tests."""

import pytest
from app import create_app
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture
def app() -> Flask:
    """Create an isolated application instance for each test."""
    return create_app("testing")


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client for the application."""
    return app.test_client()
