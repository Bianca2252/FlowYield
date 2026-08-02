"""Administration routes."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.admin import admin_bp
from app.admin.forms import UserCreateForm, UserEditForm
from app.authorization import RoleName, roles_required
from app.extensions import db
from app.models import Department, Role, User, UserRole


def populate_user_form_choices(
    form: UserCreateForm | UserEditForm,
    excluded_manager_id: int | None = None,
) -> None:
    """Populate department, manager, and role choices."""
    departments = db.session.scalars(
        select(Department)
        .where(Department.is_active.is_(True))
        .order_by(Department.name)
    ).all()

    manager_query = (
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.first_name, User.last_name)
    )

    if excluded_manager_id is not None:
        manager_query = manager_query.where(User.id != excluded_manager_id)

    managers = db.session.scalars(manager_query).all()
    roles = db.session.scalars(select(Role).order_by(Role.name)).all()

    form.department_id.choices = [
        (department.id, department.name) for department in departments
    ]
    form.manager_id.choices = [
        (0, "No manager"),
        *[(manager.id, manager.full_name) for manager in managers],
    ]
    form.role_ids.choices = [
        (role.id, role.name.replace("_", " ").title()) for role in roles
    ]


def load_selected_roles(role_ids: list[int]) -> list[Role] | None:
    """Return roles when all submitted role IDs are valid."""
    roles = db.session.scalars(select(Role).where(Role.id.in_(role_ids))).all()

    if len(roles) != len(set(role_ids)):
        return None

    return list(roles)


@admin_bp.get("/")
@roles_required(RoleName.ADMINISTRATOR)
def index():
    """Redirect Administrators to the user administration area."""
    return redirect(url_for("admin.list_users"))


@admin_bp.get("/users")
@roles_required(RoleName.ADMINISTRATOR)
def list_users():
    """Display all application users."""
    users = db.session.scalars(
        select(User)
        .options(
            selectinload(User.department),
            selectinload(User.manager),
            selectinload(User.role_assignments).selectinload(UserRole.role),
        )
        .order_by(User.first_name, User.last_name)
    ).all()

    return render_template(
        "admin/users/list.html",
        users=users,
    )


@admin_bp.route("/users/new", methods=["GET", "POST"])
@roles_required(RoleName.ADMINISTRATOR)
def create_user():
    """Create a new application user."""
    form = UserCreateForm()
    populate_user_form_choices(form)

    if form.validate_on_submit():
        existing_user = db.session.scalar(
            select(User).where(User.email == form.email.data)
        )

        if existing_user is not None:
            form.email.errors.append("A user with this email address already exists.")
            return render_template(
                "admin/users/create.html",
                form=form,
            )

        roles = load_selected_roles(form.role_ids.data)

        if roles is None:
            form.role_ids.errors.append("One or more selected roles are invalid.")
            return render_template(
                "admin/users/create.html",
                form=form,
            )

        user = User(
            email=form.email.data,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            department_id=form.department_id.data,
            manager_id=form.manager_id.data or None,
            password_hash="temporary",
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        db.session.add_all(
            [
                UserRole(
                    user=user,
                    role=role,
                    assigned_by=current_user,
                )
                for role in roles
            ]
        )
        db.session.commit()

        flash(
            f"User {user.full_name} was created successfully.",
            "success",
        )

        return redirect(url_for("admin.list_users"))

    return render_template(
        "admin/users/create.html",
        form=form,
    )


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@roles_required(RoleName.ADMINISTRATOR)
def edit_user(user_id: int):
    """Edit an existing application user."""
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    form = UserEditForm(obj=user)
    populate_user_form_choices(
        form,
        excluded_manager_id=user.id,
    )

    if not form.is_submitted():
        form.manager_id.data = user.manager_id or 0
        form.role_ids.data = [
            assignment.role_id for assignment in user.role_assignments
        ]

    if form.validate_on_submit():
        duplicate_user = db.session.scalar(
            select(User).where(
                User.email == form.email.data,
                User.id != user.id,
            )
        )

        if duplicate_user is not None:
            form.email.errors.append("A user with this email address already exists.")
            return render_template(
                "admin/users/edit.html",
                form=form,
                user=user,
            )

        roles = load_selected_roles(form.role_ids.data)

        if roles is None:
            form.role_ids.errors.append("One or more selected roles are invalid.")
            return render_template(
                "admin/users/edit.html",
                form=form,
                user=user,
            )

        selected_role_names = {role.name for role in roles}

        if user.id == current_user.id:
            if not form.is_active.data:
                form.is_active.errors.append("You cannot deactivate your own account.")

            if RoleName.ADMINISTRATOR.value not in selected_role_names:
                form.role_ids.errors.append(
                    "You cannot remove your own Administrator role."
                )

            if form.is_active.errors or form.role_ids.errors:
                return render_template(
                    "admin/users/edit.html",
                    form=form,
                    user=user,
                )

        user.email = form.email.data
        user.first_name = form.first_name.data.strip()
        user.last_name = form.last_name.data.strip()
        user.department_id = form.department_id.data
        user.manager_id = form.manager_id.data or None
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)

        user.role_assignments.clear()
        db.session.flush()

        user.role_assignments.extend(
            [
                UserRole(
                    role=role,
                    assigned_by=current_user,
                )
                for role in roles
            ]
        )

        db.session.commit()

        flash(
            f"User {user.full_name} was updated successfully.",
            "success",
        )

        return redirect(url_for("admin.list_users"))

    return render_template(
        "admin/users/edit.html",
        form=form,
        user=user,
    )


@admin_bp.post("/users/<int:user_id>/toggle-active")
@roles_required(RoleName.ADMINISTRATOR)
def toggle_user_active(user_id: int):
    """Activate or deactivate an application user."""
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    if user.id == current_user.id:
        flash(
            "You cannot deactivate your own account.",
            "error",
        )
        return redirect(url_for("admin.list_users"))

    user.is_active = not user.is_active
    db.session.commit()

    action = "activated" if user.is_active else "deactivated"

    flash(
        f"User {user.full_name} was {action}.",
        "success",
    )

    return redirect(url_for("admin.list_users"))
