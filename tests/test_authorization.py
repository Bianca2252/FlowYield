"""Tests for role-based authorization."""

import pytest
from app.authorization import RoleName, roles_required
from app.extensions import db
from app.models import Role, User, UserRole
from flask import Flask
from flask.testing import FlaskClient


def assign_role(
    app: Flask,
    user: User,
    role_name: RoleName,
) -> None:
    """Assign a role to a test user."""
    with app.app_context():
        stored_user = db.session.get(User, user.id)

        role = Role(
            name=role_name.value,
            description=f"Test role for {role_name.value}.",
        )
        assignment = UserRole(
            user=stored_user,
            role=role,
        )

        db.session.add_all([role, assignment])
        db.session.commit()


def login(client: FlaskClient, user: User) -> None:
    """Authenticate a test user."""
    response = client.post(
        "/auth/login",
        data={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 302


def test_anonymous_user_is_redirected_from_admin(
    client: FlaskClient,
) -> None:
    """Anonymous users should be redirected to the login page."""
    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_authenticated_user_without_role_receives_forbidden(
    client: FlaskClient,
    active_user: User,
) -> None:
    """An authenticated user without the required role should receive 403."""
    login(client, active_user)

    response = client.get("/admin/")

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "forbidden",
        "message": "You do not have permission to access this resource.",
    }


def test_administrator_can_access_admin_area(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """A user with the Administrator role should receive access."""
    assign_role(
        app,
        active_user,
        RoleName.ADMINISTRATOR,
    )
    login(client, active_user)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert response.get_json() == {
        "area": "administration",
        "status": "authorized",
        "user": active_user.email,
    }


def test_unrelated_role_cannot_access_admin_area(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """A role unrelated to administration should not grant access."""
    assign_role(
        app,
        active_user,
        RoleName.REQUESTER,
    )
    login(client, active_user)

    response = client.get("/admin/")

    assert response.status_code == 403


def test_roles_required_rejects_empty_role_configuration() -> None:
    """The decorator should reject a route configured without roles."""
    with pytest.raises(
        ValueError,
        match="At least one role must be provided",
    ):

        @roles_required()
        def invalid_view():
            return "invalid"


def test_role_names_use_stable_string_values() -> None:
    """Role values should remain stable for database persistence."""
    assert RoleName.ADMINISTRATOR.value == "ADMINISTRATOR"
    assert RoleName.REQUESTER.value == "REQUESTER"
    assert RoleName.PROCESS_MANAGER.value == "PROCESS_MANAGER"
