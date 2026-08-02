"""Tests for identity and organization models."""

import pytest
from app.extensions import db
from app.models import Department, Role, User, UserRole
from flask import Flask
from sqlalchemy.exc import IntegrityError


def create_department() -> Department:
    """Create a default test department."""
    department = Department(
        name="Operations",
        code="OPS",
    )
    db.session.add(department)
    db.session.flush()

    return department


def create_user(
    department: Department,
    email: str = "user@aurevia.example",
) -> User:
    """Create a default test user."""
    user = User(
        email=email,
        first_name="Alex",
        last_name="Morgan",
        department=department,
        password_hash="temporary",
    )
    user.set_password("StrongPassword123!")

    db.session.add(user)
    db.session.flush()

    return user


def test_department_can_be_created(app: Flask) -> None:
    """A department should persist with active state enabled."""
    with app.app_context():
        department = create_department()
        db.session.commit()

        assert department.id is not None
        assert department.name == "Operations"
        assert department.code == "OPS"
        assert department.is_active is True


def test_department_name_must_be_unique(app: Flask) -> None:
    """Duplicate department names should be rejected."""
    with app.app_context():
        db.session.add_all(
            [
                Department(name="Operations", code="OPS"),
                Department(name="Operations", code="OPS-2"),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_user_password_is_hashed(app: Flask) -> None:
    """A stored password should be hashed and verifiable."""
    with app.app_context():
        department = create_department()
        user = create_user(department)

        db.session.commit()

        assert user.password_hash != "StrongPassword123!"
        assert user.check_password("StrongPassword123!") is True
        assert user.check_password("wrong-password") is False


def test_empty_password_is_rejected(app: Flask) -> None:
    """An empty password should not be accepted."""
    with app.app_context():
        department = create_department()
        user = User(
            email="empty-password@aurevia.example",
            first_name="Jamie",
            last_name="Taylor",
            department=department,
            password_hash="temporary",
        )

        with pytest.raises(ValueError, match="Password must not be empty"):
            user.set_password("")


def test_user_can_report_to_manager(app: Flask) -> None:
    """A user should support a self-referential manager relationship."""
    with app.app_context():
        department = create_department()
        manager = create_user(
            department,
            email="manager@aurevia.example",
        )
        employee = create_user(
            department,
            email="employee@aurevia.example",
        )
        employee.manager = manager

        db.session.commit()

        assert employee.manager == manager
        assert employee in manager.direct_reports


def test_user_cannot_be_their_own_manager(app: Flask) -> None:
    """The database should reject self-management."""
    with app.app_context():
        department = create_department()
        user = create_user(department)

        db.session.commit()

        user.manager_id = user.id

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_role_assignment_supports_metadata(app: Flask) -> None:
    """A role assignment should preserve assignment metadata."""
    with app.app_context():
        department = create_department()
        administrator = create_user(
            department,
            email="admin@aurevia.example",
        )
        requester = create_user(
            department,
            email="requester@aurevia.example",
        )
        role = Role(
            name="REQUESTER",
            description="Can create purchase requests.",
        )

        assignment = UserRole(
            user=requester,
            role=role,
            assigned_by=administrator,
        )

        db.session.add_all([role, assignment])
        db.session.commit()

        assert requester.has_role("REQUESTER") is True
        assert assignment.assigned_by == administrator
        assert assignment.assigned_at is not None


def test_duplicate_role_assignment_is_rejected(app: Flask) -> None:
    """A user should not receive the same role twice."""
    with app.app_context():
        department = create_department()
        user = create_user(department)
        role = Role(name="REQUESTER")

        db.session.add(role)
        db.session.flush()

        db.session.add_all(
            [
                UserRole(user=user, role=role),
                UserRole(user=user, role=role),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_user_full_name(app: Flask) -> None:
    """The full name property should combine first and last name."""
    with app.app_context():
        department = create_department()
        user = create_user(department)

        assert user.full_name == "Alex Morgan"
