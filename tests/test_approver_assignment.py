"""Tests for workflow approver assignment."""

from decimal import Decimal

import pytest
from app.authorization import RoleName
from app.extensions import db
from app.models import (
    Role,
    StepConfiguration,
    StepType,
    User,
    UserRole,
    WorkflowConfiguration,
)
from app.workflows.assignments import assign_approval_path
from app.workflows.exceptions import (
    ApproverAssignmentError,
    InactiveApproverError,
    InvalidApproverRoleError,
    MissingManagerError,
    SelfApprovalError,
)
from app.workflows.rules import ApprovalPathStep
from flask import Flask
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
    """Assign a role without creating duplicate role records."""
    role = get_or_create_role(role_name)

    existing_assignment = db.session.scalar(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
        )
    )

    if existing_assignment is None:
        db.session.add(
            UserRole(
                user=user,
                role=role,
            )
        )
        db.session.flush()


def create_user(
    *,
    email: str,
    department_id: int,
    first_name: str,
    last_name: str,
    is_active: bool = True,
) -> User:
    """Create a user for assignment tests."""
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        department_id=department_id,
        is_active=is_active,
        password_hash="temporary",
    )
    user.set_password("StrongPassword123!")

    db.session.add(user)
    db.session.flush()

    return user


def create_configuration(
    *,
    creator: User,
    finance_approver: User | None = None,
    it_reviewer: User | None = None,
    director_approver: User | None = None,
) -> WorkflowConfiguration:
    """Create a complete workflow configuration."""
    configuration = WorkflowConfiguration(
        version_number=1,
        name="Assignment test configuration",
        low_value_threshold=Decimal("1000.00"),
        high_value_threshold=Decimal("10000.00"),
        it_review_threshold=Decimal("5000.00"),
        created_by_user_id=creator.id,
        is_active=True,
    )

    configuration.step_configurations.extend(
        [
            StepConfiguration(
                step_type=StepType.MANAGER_APPROVAL,
                sla_duration_hours=24,
                required_role_name=RoleName.MANAGER_APPROVER.value,
                sequence_hint=1,
            ),
            StepConfiguration(
                step_type=StepType.IT_REVIEW,
                sla_duration_hours=36,
                required_role_name=RoleName.IT_REVIEWER.value,
                sequence_hint=2,
                default_assignee=it_reviewer,
            ),
            StepConfiguration(
                step_type=StepType.FINANCE_APPROVAL,
                sla_duration_hours=48,
                required_role_name=RoleName.FINANCE_APPROVER.value,
                sequence_hint=3,
                default_assignee=finance_approver,
            ),
            StepConfiguration(
                step_type=StepType.DIRECTOR_APPROVAL,
                sla_duration_hours=72,
                required_role_name=RoleName.DIRECTOR_APPROVER.value,
                sequence_hint=4,
                default_assignee=director_approver,
            ),
        ]
    )

    db.session.add(configuration)
    db.session.flush()

    return configuration


def path_step(
    step_type: StepType,
    sequence_number: int,
) -> ApprovalPathStep:
    """Create a generated approval path step."""
    return ApprovalPathStep(
        step_type=step_type,
        sequence_number=sequence_number,
        reason_for_inclusion=f"{step_type.value} is required.",
    )


def test_manager_step_is_assigned_to_requesters_manager(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Manager Approval should use the requester's manager."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        manager = create_user(
            email="manager@aurevia.example",
            department_id=department.id,
            first_name="Morgan",
            last_name="Manager",
        )
        assign_role(manager, RoleName.MANAGER_APPROVER)

        requester.manager = manager

        configuration = create_configuration(
            creator=requester,
        )

        assigned_steps = assign_approval_path(
            requester=requester,
            approval_path=[
                path_step(StepType.MANAGER_APPROVAL, 1),
            ],
            workflow_configuration=configuration,
        )

        assert len(assigned_steps) == 1
        assert assigned_steps[0].assigned_user == manager
        assert assigned_steps[0].required_role_name == RoleName.MANAGER_APPROVER.value
        assert assigned_steps[0].sla_duration_hours == 24


def test_missing_manager_blocks_assignment(
    app: Flask,
    active_user: User,
) -> None:
    """A requester without a manager should not receive a workflow."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        requester.manager = None

        configuration = create_configuration(
            creator=requester,
        )

        with pytest.raises(
            MissingManagerError,
            match="does not have a configured manager",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.MANAGER_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_inactive_manager_is_rejected(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """An inactive manager should not receive an approval step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        manager = create_user(
            email="inactive.manager@aurevia.example",
            department_id=department.id,
            first_name="Inactive",
            last_name="Manager",
            is_active=False,
        )
        assign_role(manager, RoleName.MANAGER_APPROVER)
        requester.manager = manager

        configuration = create_configuration(
            creator=requester,
        )

        with pytest.raises(
            InactiveApproverError,
            match="inactive",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.MANAGER_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_manager_without_required_role_is_rejected(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """The requester's manager must hold Manager Approver."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        manager = create_user(
            email="wrong.role.manager@aurevia.example",
            department_id=department.id,
            first_name="Wrong",
            last_name="Role",
        )
        requester.manager = manager

        configuration = create_configuration(
            creator=requester,
        )

        with pytest.raises(
            InvalidApproverRoleError,
            match="MANAGER_APPROVER",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.MANAGER_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_finance_step_uses_configured_default_assignee(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Finance Approval should use its configured default user."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        finance_approver = create_user(
            email="finance@aurevia.example",
            department_id=department.id,
            first_name="Fiona",
            last_name="Finance",
        )
        assign_role(
            finance_approver,
            RoleName.FINANCE_APPROVER,
        )

        configuration = create_configuration(
            creator=requester,
            finance_approver=finance_approver,
        )

        assigned_steps = assign_approval_path(
            requester=requester,
            approval_path=[
                path_step(StepType.FINANCE_APPROVAL, 1),
            ],
            workflow_configuration=configuration,
        )

        assert assigned_steps[0].assigned_user == finance_approver
        assert assigned_steps[0].sla_duration_hours == 48


def test_it_step_uses_configured_default_assignee(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """IT Review should use its configured default reviewer."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        it_reviewer = create_user(
            email="it.reviewer@aurevia.example",
            department_id=department.id,
            first_name="Isaac",
            last_name="IT",
        )
        assign_role(it_reviewer, RoleName.IT_REVIEWER)

        configuration = create_configuration(
            creator=requester,
            it_reviewer=it_reviewer,
        )

        assigned_steps = assign_approval_path(
            requester=requester,
            approval_path=[
                path_step(StepType.IT_REVIEW, 1),
            ],
            workflow_configuration=configuration,
        )

        assert assigned_steps[0].assigned_user == it_reviewer
        assert assigned_steps[0].sla_duration_hours == 36


def test_director_step_uses_configured_default_assignee(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Director Approval should use its configured default user."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        director = create_user(
            email="director@aurevia.example",
            department_id=department.id,
            first_name="Diana",
            last_name="Director",
        )
        assign_role(director, RoleName.DIRECTOR_APPROVER)

        configuration = create_configuration(
            creator=requester,
            director_approver=director,
        )

        assigned_steps = assign_approval_path(
            requester=requester,
            approval_path=[
                path_step(StepType.DIRECTOR_APPROVAL, 1),
            ],
            workflow_configuration=configuration,
        )

        assert assigned_steps[0].assigned_user == director
        assert assigned_steps[0].sla_duration_hours == 72


def test_missing_default_assignee_blocks_assignment(
    app: Flask,
    active_user: User,
) -> None:
    """A role-based step requires a configured default approver."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        configuration = create_configuration(
            creator=requester,
        )

        with pytest.raises(
            ApproverAssignmentError,
            match="No default approver",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.FINANCE_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_self_approval_is_rejected(
    app: Flask,
    active_user: User,
) -> None:
    """The requester must not receive their own approval step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        assign_role(requester, RoleName.FINANCE_APPROVER)

        configuration = create_configuration(
            creator=requester,
            finance_approver=requester,
        )

        with pytest.raises(
            SelfApprovalError,
            match="requester cannot perform",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.FINANCE_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_default_assignee_with_wrong_role_is_rejected(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A configured default user must hold the step's role."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        wrong_user = create_user(
            email="wrong.finance@aurevia.example",
            department_id=department.id,
            first_name="Wrong",
            last_name="Finance",
        )
        assign_role(wrong_user, RoleName.IT_REVIEWER)

        configuration = create_configuration(
            creator=requester,
            finance_approver=wrong_user,
        )

        with pytest.raises(
            InvalidApproverRoleError,
            match="FINANCE_APPROVER",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.FINANCE_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_disabled_step_configuration_is_rejected(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A generated path cannot use a disabled step configuration."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        finance_approver = create_user(
            email="disabled.finance@aurevia.example",
            department_id=department.id,
            first_name="Disabled",
            last_name="Finance",
        )
        assign_role(
            finance_approver,
            RoleName.FINANCE_APPROVER,
        )

        configuration = create_configuration(
            creator=requester,
            finance_approver=finance_approver,
        )

        finance_configuration = next(
            step_configuration
            for step_configuration in configuration.step_configurations
            if step_configuration.step_type == StepType.FINANCE_APPROVAL
        )
        finance_configuration.is_enabled = False

        with pytest.raises(
            ApproverAssignmentError,
            match="No enabled configuration",
        ):
            assign_approval_path(
                requester=requester,
                approval_path=[
                    path_step(StepType.FINANCE_APPROVAL, 1),
                ],
                workflow_configuration=configuration,
            )


def test_complete_path_preserves_order_and_assignments(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A complete path should retain ordering, roles, and assignees."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        manager = create_user(
            email="complete.manager@aurevia.example",
            department_id=department.id,
            first_name="Complete",
            last_name="Manager",
        )
        it_reviewer = create_user(
            email="complete.it@aurevia.example",
            department_id=department.id,
            first_name="Complete",
            last_name="IT",
        )
        finance_approver = create_user(
            email="complete.finance@aurevia.example",
            department_id=department.id,
            first_name="Complete",
            last_name="Finance",
        )
        director = create_user(
            email="complete.director@aurevia.example",
            department_id=department.id,
            first_name="Complete",
            last_name="Director",
        )

        assign_role(manager, RoleName.MANAGER_APPROVER)
        assign_role(it_reviewer, RoleName.IT_REVIEWER)
        assign_role(
            finance_approver,
            RoleName.FINANCE_APPROVER,
        )
        assign_role(director, RoleName.DIRECTOR_APPROVER)

        requester.manager = manager

        configuration = create_configuration(
            creator=requester,
            finance_approver=finance_approver,
            it_reviewer=it_reviewer,
            director_approver=director,
        )

        assigned_steps = assign_approval_path(
            requester=requester,
            approval_path=[
                path_step(StepType.MANAGER_APPROVAL, 1),
                path_step(StepType.IT_REVIEW, 2),
                path_step(StepType.FINANCE_APPROVAL, 3),
                path_step(StepType.DIRECTOR_APPROVAL, 4),
            ],
            workflow_configuration=configuration,
        )

        assert [assigned_step.step_type for assigned_step in assigned_steps] == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
            StepType.DIRECTOR_APPROVAL,
        ]

        assert [assigned_step.sequence_number for assigned_step in assigned_steps] == [
            1,
            2,
            3,
            4,
        ]

        assert [assigned_step.assigned_user for assigned_step in assigned_steps] == [
            manager,
            it_reviewer,
            finance_approver,
            director,
        ]
