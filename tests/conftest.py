"""Shared pytest fixtures for FlowYield tests."""

from collections.abc import Generator

import pytest
from app import create_app
from app.extensions import db
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture
def app() -> Generator[Flask]:
    """Create an isolated application instance for each test."""
    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client for the application."""
    return app.test_client()
