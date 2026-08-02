"""Tests for user administration."""

from app.authorization import RoleName
from app.extensions import db
from app.models import Department, Role, User, UserRole
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select


def assign_administrator_role(
    app: Flask,
    user: User,
) -> Role:
    """Assign the Administrator role to a test user."""
    with app.app_context():
        stored_user = db.session.get(User, user.id)

        role = Role(
            name=RoleName.ADMINISTRATOR.value,
            description="Can manage FlowYield users.",
        )
        assignment = UserRole(
            user=stored_user,
            role=role,
        )

        db.session.add_all([role, assignment])
        db.session.commit()
        db.session.refresh(role)

        return role


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


def test_administrator_can_view_user_list(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """An Administrator should see the user administration list."""
    assign_administrator_role(app, active_user)
    login(client, active_user)

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"User administration" in response.data
    assert active_user.email.encode() in response.data


def test_non_administrator_cannot_view_user_list(
    client: FlaskClient,
    active_user: User,
) -> None:
    """A user without the Administrator role should receive 403."""
    login(client, active_user)

    response = client.get("/admin/users")

    assert response.status_code == 403


def test_administrator_can_open_create_user_form(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """An Administrator should access the user creation form."""
    assign_administrator_role(app, active_user)
    login(client, active_user)

    response = client.get("/admin/users/new")

    assert response.status_code == 200
    assert b"Create user" in response.data


def test_administrator_can_create_user(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An Administrator should create a user with assigned roles."""
    administrator_role = assign_administrator_role(
        app,
        active_user,
    )

    with app.app_context():
        requester_role = Role(
            name=RoleName.REQUESTER.value,
            description="Can create purchase requests.",
        )
        db.session.add(requester_role)
        db.session.commit()

        requester_role_id = requester_role.id
        department_id = department.id

    login(client, active_user)

    response = client.post(
        "/admin/users/new",
        data={
            "email": "new.user@aurevia.example",
            "first_name": "New",
            "last_name": "User",
            "password": "TemporaryPassword123!",
            "department_id": department_id,
            "manager_id": active_user.id,
            "role_ids": [requester_role_id],
            "is_active": "y",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/users")

    with app.app_context():
        created_user = db.session.scalar(
            select(User).where(User.email == "new.user@aurevia.example")
        )

        assert created_user is not None
        assert created_user.full_name == "New User"
        assert created_user.department_id == department_id
        assert created_user.manager_id == active_user.id
        assert created_user.is_active is True
        assert created_user.check_password("TemporaryPassword123!")
        assert created_user.has_role(RoleName.REQUESTER.value)

        assignment = db.session.scalar(
            select(UserRole).where(UserRole.user_id == created_user.id)
        )

        assert assignment is not None
        assert assignment.assigned_by_user_id == active_user.id
        assert administrator_role.id is not None


def test_duplicate_user_email_is_rejected(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An existing email address should not be accepted twice."""
    administrator_role = assign_administrator_role(
        app,
        active_user,
    )

    login(client, active_user)

    response = client.post(
        "/admin/users/new",
        data={
            "email": active_user.email.upper(),
            "first_name": "Duplicate",
            "last_name": "User",
            "password": "TemporaryPassword123!",
            "department_id": department.id,
            "manager_id": 0,
            "role_ids": [administrator_role.id],
            "is_active": "y",
        },
    )

    assert response.status_code == 200
    assert b"A user with this email address already exists." in response.data

    with app.app_context():
        matching_users = db.session.scalars(
            select(User).where(User.email == active_user.email)
        ).all()

        assert len(matching_users) == 1


def test_administrator_can_edit_user(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    inactive_user: User,
    department: Department,
) -> None:
    """An Administrator should update another user's account."""
    administrator_role = assign_administrator_role(
        app,
        active_user,
    )

    with app.app_context():
        requester_role = Role(
            name=RoleName.REQUESTER.value,
        )
        db.session.add(requester_role)
        db.session.commit()

        requester_role_id = requester_role.id
        administrator_role_id = administrator_role.id
        department_id = department.id
        inactive_user_id = inactive_user.id

    login(client, active_user)

    response = client.post(
        f"/admin/users/{inactive_user_id}/edit",
        data={
            "email": "updated.user@aurevia.example",
            "first_name": "Updated",
            "last_name": "Employee",
            "password": "UpdatedPassword123!",
            "department_id": department_id,
            "manager_id": active_user.id,
            "role_ids": [requester_role_id],
            "is_active": "y",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/users")

    with app.app_context():
        updated_user = db.session.get(User, inactive_user_id)

        assert updated_user is not None
        assert updated_user.email == "updated.user@aurevia.example"
        assert updated_user.full_name == "Updated Employee"
        assert updated_user.manager_id == active_user.id
        assert updated_user.is_active is True
        assert updated_user.check_password("UpdatedPassword123!")
        assert updated_user.has_role(RoleName.REQUESTER.value)
        assert not updated_user.has_role(RoleName.ADMINISTRATOR.value)
        assert administrator_role_id is not None


def test_administrator_can_deactivate_another_user(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    inactive_user: User,
) -> None:
    """An Administrator should toggle another user's active state."""
    assign_administrator_role(app, active_user)

    with app.app_context():
        stored_user = db.session.get(User, inactive_user.id)
        stored_user.is_active = True
        db.session.commit()
        user_id = stored_user.id

    login(client, active_user)

    response = client.post(
        f"/admin/users/{user_id}/toggle-active",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        updated_user = db.session.get(User, user_id)

        assert updated_user is not None
        assert updated_user.is_active is False


def test_administrator_cannot_deactivate_own_account(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """An Administrator should not deactivate their own account."""
    assign_administrator_role(app, active_user)
    login(client, active_user)

    response = client.post(
        f"/admin/users/{active_user.id}/toggle-active",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        assert stored_user is not None
        assert stored_user.is_active is True


def test_administrator_cannot_remove_own_admin_role(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An Administrator should retain their own administrative access."""
    administrator_role = assign_administrator_role(
        app,
        active_user,
    )

    with app.app_context():
        requester_role = Role(
            name=RoleName.REQUESTER.value,
        )
        db.session.add(requester_role)
        db.session.commit()

        requester_role_id = requester_role.id
        department_id = department.id
        administrator_role_id = administrator_role.id

    login(client, active_user)

    response = client.post(
        f"/admin/users/{active_user.id}/edit",
        data={
            "email": active_user.email,
            "first_name": active_user.first_name,
            "last_name": active_user.last_name,
            "password": "",
            "department_id": department_id,
            "manager_id": 0,
            "role_ids": [requester_role_id],
            "is_active": "y",
        },
    )

    assert response.status_code == 200
    assert b"You cannot remove your own Administrator role." in response.data

    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        assert stored_user is not None
        assert stored_user.has_role(RoleName.ADMINISTRATOR.value)
        assert administrator_role_id is not None


def test_editing_unknown_user_returns_not_found(
    app: Flask,
    client: FlaskClient,
    active_user: User,
) -> None:
    """Editing an unknown user should return 404."""
    assign_administrator_role(app, active_user)
    login(client, active_user)

    response = client.get("/admin/users/999999/edit")

    assert response.status_code == 404
