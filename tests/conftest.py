"""Shared pytest fixtures for FlowYield tests."""

from collections.abc import Generator

import pytest
from app import create_app
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture
def app() -> Generator[Flask]:
    """Create an isolated application instance for each test."""
    test_app = create_app("testing")

    yield test_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client for the application."""
    return app.test_client()
