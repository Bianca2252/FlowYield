"""Tests for application authentication."""

from app.extensions import db
from app.models import User
from flask import Flask
from flask.testing import FlaskClient


def test_login_page_is_available(client: FlaskClient) -> None:
    """The login page should be available to anonymous users."""
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"Sign in to FlowYield" in response.data


def test_valid_user_can_log_in(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """An active user with valid credentials should be authenticated."""
    response = client.post(
        "/auth/login",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        assert stored_user is not None
        assert stored_user.last_login_at is not None


def test_authenticated_user_can_access_dashboard(
    client: FlaskClient,
    active_user: User,
) -> None:
    """An authenticated user should access the protected dashboard."""
    client.post(
        "/auth/login",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "FlowYield",
        "user": active_user.email,
        "status": "authenticated",
    }


def test_invalid_password_is_rejected(
    client: FlaskClient,
    active_user: User,
) -> None:
    """An invalid password should not create an authenticated session."""
    response = client.post(
        "/auth/login",
        data={
            "email": active_user.email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_unknown_email_is_rejected(client: FlaskClient) -> None:
    """An unknown email address should be rejected safely."""
    response = client.post(
        "/auth/login",
        data={
            "email": "unknown@aurevia.example",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_inactive_user_cannot_log_in(
    client: FlaskClient,
    inactive_user: User,
) -> None:
    """An inactive user should not receive an authenticated session."""
    response = client.post(
        "/auth/login",
        data={
            "email": inactive_user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_anonymous_user_is_redirected_to_login(
    client: FlaskClient,
) -> None:
    """Anonymous users should be redirected from protected routes."""
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert "next=" in response.headers["Location"]


def test_authenticated_user_is_redirected_from_login(
    client: FlaskClient,
    active_user: User,
) -> None:
    """Authenticated users should not see the login form again."""
    client.post(
        "/auth/login",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
    )

    response = client.get("/auth/login")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_user_can_log_out(
    client: FlaskClient,
    active_user: User,
) -> None:
    """An authenticated user should be able to end their session."""
    client.post(
        "/auth/login",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
    )

    logout_response = client.post(
        "/auth/logout",
        follow_redirects=False,
    )

    assert logout_response.status_code == 302
    assert logout_response.headers["Location"].endswith("/auth/login")

    dashboard_response = client.get("/dashboard")

    assert dashboard_response.status_code == 302
    assert "/auth/login" in dashboard_response.headers["Location"]


def test_external_next_url_is_ignored(
    client: FlaskClient,
    active_user: User,
) -> None:
    """Login should not redirect users to an external website."""
    response = client.post(
        "/auth/login?next=https://malicious.example",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_safe_internal_next_url_is_used(
    client: FlaskClient,
    active_user: User,
) -> None:
    """Login may redirect to a safe path on the current host."""
    response = client.post(
        "/auth/login?next=/dashboard",
        data={
            "email": active_user.email,
            "password": "StrongPassword123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_email_is_normalized_before_login(
    client: FlaskClient,
    active_user: User,
) -> None:
    """Login should normalize surrounding spaces and letter casing."""
    response = client.post(
        "/auth/login",
        data={
            "email": f"  {active_user.email.upper()}  ",
            "password": "StrongPassword123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
