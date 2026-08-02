"""Tests for purchase request draft management."""

from decimal import Decimal

from app.authorization import RoleName
from app.extensions import db
from app.models import (
    Department,
    PurchaseRequest,
    RequestStatus,
    Role,
    User,
    UserRole,
)
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select


def assign_requester_role(
    app: Flask,
    user: User,
) -> None:
    """Assign the Requester role to a test user."""
    with app.app_context():
        stored_user = db.session.get(User, user.id)

        role = db.session.scalar(
            select(Role).where(Role.name == RoleName.REQUESTER.value)
        )

        if role is None:
            role = Role(name=RoleName.REQUESTER.value)
            db.session.add(role)
            db.session.flush()

        existing_assignment = db.session.scalar(
            select(UserRole).where(
                UserRole.user_id == stored_user.id,
                UserRole.role_id == role.id,
            )
        )

        if existing_assignment is None:
            db.session.add(
                UserRole(
                    user=stored_user,
                    role=role,
                )
            )

        db.session.commit()


def create_second_user(
    app: Flask,
    department: Department,
) -> int:
    """Create another Requester for ownership tests."""
    with app.app_context():
        role = db.session.scalar(
            select(Role).where(Role.name == RoleName.REQUESTER.value)
        )

        if role is None:
            role = Role(name=RoleName.REQUESTER.value)
            db.session.add(role)
            db.session.flush()

        user = User(
            email="second.user@aurevia.example",
            first_name="Second",
            last_name="User",
            department_id=department.id,
            password_hash="temporary",
        )
        user.set_password("StrongPassword123!")

        db.session.add(user)
        db.session.flush()

        db.session.add(
            UserRole(
                user=user,
                role=role,
            )
        )
        db.session.commit()

        return user.id


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


def test_requester_can_open_request_list(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """A Requester should access their request list."""
    assign_requester_role(app, active_user)
    login(client, active_user)

    response = client.get("/requests/")

    assert response.status_code == 200
    assert b"My purchase requests" in response.data


def test_user_without_requester_role_is_forbidden(
    client: FlaskClient,
    active_user: User,
) -> None:
    """A user without Requester access should receive 403."""
    login(client, active_user)

    response = client.get("/requests/")

    assert response.status_code == 403


def test_requester_can_create_incomplete_draft(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """A Requester should save an incomplete draft."""
    assign_requester_role(app, active_user)
    login(client, active_user)

    response = client.post(
        "/requests/new",
        data={
            "title": "Future equipment purchase",
            "description": "",
            "business_justification": "",
            "category": "",
            "supplier": "",
            "requested_amount": "",
            "expected_purchase_date": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        purchase_request = db.session.scalar(
            select(PurchaseRequest).where(
                PurchaseRequest.requester_id == active_user.id
            )
        )

        assert purchase_request is not None
        assert purchase_request.status == RequestStatus.DRAFT
        assert purchase_request.title == "Future equipment purchase"
        assert purchase_request.requested_amount is None
        assert purchase_request.revisions == []


def test_requester_can_edit_own_draft(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A Requester should update their own draft."""
    assign_requester_role(app, active_user)

    with app.app_context():
        purchase_request = PurchaseRequest(
            requester_id=active_user.id,
            department_id=department.id,
            title="Old title",
        )
        db.session.add(purchase_request)
        db.session.commit()

        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/edit",
        data={
            "title": "Updated laptop request",
            "description": "Updated description",
            "business_justification": "Required for development.",
            "category": "HARDWARE",
            "supplier": "Hardware Partner",
            "requested_amount": "2500.00",
            "expected_purchase_date": "2026-10-01",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        updated_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert updated_request is not None
        assert updated_request.title == "Updated laptop request"
        assert updated_request.requested_amount == Decimal("2500.00")
        assert updated_request.status == RequestStatus.DRAFT


def test_requester_cannot_view_another_users_request(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An unrelated Requester should receive 404."""
    assign_requester_role(app, active_user)
    other_user_id = create_second_user(app, department)

    with app.app_context():
        purchase_request = PurchaseRequest(
            requester_id=other_user_id,
            department_id=department.id,
            title="Private request",
        )
        db.session.add(purchase_request)
        db.session.commit()

        request_id = purchase_request.id

    login(client, active_user)

    response = client.get(f"/requests/{request_id}")

    assert response.status_code == 404


def test_requester_cannot_edit_cancelled_request(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A cancelled request should no longer be editable."""
    assign_requester_role(app, active_user)

    with app.app_context():
        purchase_request = PurchaseRequest(
            requester_id=active_user.id,
            department_id=department.id,
            status=RequestStatus.CANCELLED,
        )
        db.session.add(purchase_request)
        db.session.commit()

        request_id = purchase_request.id

    login(client, active_user)

    response = client.get(f"/requests/{request_id}/edit")

    assert response.status_code == 409


def test_requester_can_cancel_own_draft(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A Requester should cancel their own draft."""
    assign_requester_role(app, active_user)

    with app.app_context():
        purchase_request = PurchaseRequest(
            requester_id=active_user.id,
            department_id=department.id,
        )
        db.session.add(purchase_request)
        db.session.commit()

        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/cancel",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        cancelled_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert cancelled_request is not None
        assert cancelled_request.status == RequestStatus.CANCELLED
        assert cancelled_request.cancelled_at is not None
        assert cancelled_request.revisions == []


def test_request_list_contains_only_owned_requests(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """The request list should not expose another user's requests."""
    assign_requester_role(app, active_user)
    other_user_id = create_second_user(app, department)

    with app.app_context():
        db.session.add_all(
            [
                PurchaseRequest(
                    requester_id=active_user.id,
                    department_id=department.id,
                    title="Visible request",
                ),
                PurchaseRequest(
                    requester_id=other_user_id,
                    department_id=department.id,
                    title="Hidden request",
                ),
            ]
        )
        db.session.commit()

    login(client, active_user)

    response = client.get("/requests/")

    assert response.status_code == 200
    assert b"Visible request" in response.data
    assert b"Hidden request" not in response.data


def test_request_list_can_filter_by_status(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A Requester should filter their requests by status."""
    assign_requester_role(app, active_user)

    with app.app_context():
        db.session.add_all(
            [
                PurchaseRequest(
                    requester_id=active_user.id,
                    department_id=department.id,
                    title="Draft request",
                    status=RequestStatus.DRAFT,
                ),
                PurchaseRequest(
                    requester_id=active_user.id,
                    department_id=department.id,
                    title="Cancelled request",
                    status=RequestStatus.CANCELLED,
                ),
            ]
        )
        db.session.commit()

    login(client, active_user)

    response = client.get("/requests/?status=CANCELLED")

    assert response.status_code == 200
    assert b"Cancelled request" in response.data
    assert b"Draft request" not in response.data
