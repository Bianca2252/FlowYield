"""Tests for the role-aware FlowYield dashboard."""

from datetime import date
from decimal import Decimal

from app.authorization import RoleName
from app.extensions import db
from app.models import (
    Department,
    PurchaseRequest,
    RequestCategory,
    RequestStatus,
    Role,
    User,
    UserRole,
)
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select


def get_or_create_role(role_name: RoleName) -> Role:
    """Return an existing role or create it."""
    role = db.session.scalar(select(Role).where(Role.name == role_name.value))

    if role is None:
        role = Role(
            name=role_name.value,
            description=f"Test role for {role_name.value}.",
        )
        db.session.add(role)
        db.session.flush()

    return role


def assign_role(
    user: User,
    role_name: RoleName,
) -> None:
    """Assign a role to a user."""
    role = get_or_create_role(role_name)

    assignment = db.session.scalar(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
        )
    )

    if assignment is None:
        db.session.add(
            UserRole(
                user=user,
                role=role,
            )
        )
        db.session.commit()


def login(
    client: FlaskClient,
    user: User,
) -> None:
    """Authenticate a test user."""
    response = client.post(
        "/auth/login",
        data={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 302


def create_request(
    *,
    requester: User,
    department: Department,
    title: str,
    status: RequestStatus,
) -> PurchaseRequest:
    """Create a purchase request for dashboard tests."""
    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=department.id,
        title=title,
        description="Dashboard test request.",
        business_justification="Required for dashboard testing.",
        category=RequestCategory.HARDWARE,
        supplier="Dashboard Supplier",
        requested_amount=Decimal("2500.00"),
        currency="EUR",
        expected_purchase_date=date(2026, 10, 1),
        status=status,
    )

    db.session.add(purchase_request)
    db.session.commit()

    return purchase_request


def test_anonymous_user_can_open_landing_page(
    client: FlaskClient,
) -> None:
    """Anonymous visitors should see the FlowYield landing page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"FlowYield" in response.data
    assert b"Sign in" in response.data


def test_dashboard_requires_authentication(
    client: FlaskClient,
) -> None:
    """Unauthenticated visitors should be redirected to login."""
    response = client.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_requester_dashboard_displays_request_metrics(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A requester should see request totals and recent requests."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )
        assign_role(
            requester,
            RoleName.REQUESTER,
        )

        create_request(
            requester=requester,
            department=department,
            title="Dashboard draft request",
            status=RequestStatus.DRAFT,
        )
        create_request(
            requester=requester,
            department=department,
            title="Dashboard approved request",
            status=RequestStatus.APPROVED,
        )

    login(
        client,
        active_user,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"My purchase requests" in response.data
    assert b"Dashboard draft request" in response.data
    assert b"Dashboard approved request" in response.data
    assert b"Create request" in response.data


def test_approver_dashboard_displays_workload_section(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """An approver should see approval workload information."""
    with app.app_context():
        user = db.session.get(
            User,
            active_user.id,
        )
        assign_role(
            user,
            RoleName.MANAGER_APPROVER,
        )

    login(
        client,
        active_user,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Approval workload" in response.data
    assert b"Active tasks" in response.data
    assert b"Overdue tasks" in response.data
    assert b"Open approval inbox" in response.data


def test_user_without_dashboard_roles_sees_empty_state(
    client: FlaskClient,
    active_user: User,
) -> None:
    """A user without operational roles should see a safe empty state."""
    login(
        client,
        active_user,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"No dashboard information is available" in response.data
