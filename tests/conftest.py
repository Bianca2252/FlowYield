"""Shared pytest fixtures for FlowYield tests."""

from collections.abc import Generator

import pytest
from app import create_app
from app.extensions import db
from app.models import Department, User
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


@pytest.fixture
def department(app: Flask) -> Department:
    """Create a department for authentication tests."""
    with app.app_context():
        department = Department(
            name="Operations",
            code="OPS",
        )
        db.session.add(department)
        db.session.commit()
        db.session.refresh(department)

        return department


@pytest.fixture
def active_user(app: Flask, department: Department) -> User:
    """Create an active application user."""
    with app.app_context():
        user = User(
            email="alex.morgan@aurevia.example",
            first_name="Alex",
            last_name="Morgan",
            department_id=department.id,
            password_hash="temporary",
            is_active=True,
        )
        user.set_password("StrongPassword123!")

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        return user


@pytest.fixture
def inactive_user(app: Flask, department: Department) -> User:
    """Create an inactive application user."""
    with app.app_context():
        user = User(
            email="inactive.user@aurevia.example",
            first_name="Inactive",
            last_name="User",
            department_id=department.id,
            password_hash="temporary",
            is_active=False,
        )
        user.set_password("StrongPassword123!")

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        return user
