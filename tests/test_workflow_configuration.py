"""Tests for versioned workflow configuration."""

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
from app.workflows.configuration_service import (
    activate_workflow_configuration,
    create_workflow_configuration,
    get_active_workflow_configuration,
)
from app.workflows.exceptions import WorkflowConfigurationError
from flask import Flask
from sqlalchemy.exc import IntegrityError


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

        db.session.add(role)
        db.session.flush()

        db.session.add(
            UserRole(
                user=stored_user,
                role=role,
            )
        )
        db.session.commit()


def build_step(
    *,
    step_type: StepType,
    role_name: RoleName,
    sequence_hint: int,
    sla_duration_hours: int = 24,
    default_assignee: User | None = None,
) -> StepConfiguration:
    """Build a workflow step configuration."""
    return StepConfiguration(
        step_type=step_type,
        sla_duration_hours=sla_duration_hours,
        required_role_name=role_name.value,
        sequence_hint=sequence_hint,
        default_assignee=default_assignee,
    )


def test_workflow_configuration_defaults(
    app: Flask,
    active_user: User,
) -> None:
    """A configuration should store versioned monetary thresholds."""
    with app.app_context():
        configuration = WorkflowConfiguration(
            version_number=1,
            name="Default purchase approval",
            low_value_threshold=Decimal("1000.00"),
            high_value_threshold=Decimal("10000.00"),
            it_review_threshold=Decimal("5000.00"),
            created_by_user_id=active_user.id,
        )

        db.session.add(configuration)
        db.session.commit()

        assert configuration.id is not None
        assert configuration.version_number == 1
        assert configuration.low_value_threshold == Decimal("1000.00")
        assert configuration.high_value_threshold == Decimal("10000.00")
        assert configuration.it_review_threshold == Decimal("5000.00")
        assert configuration.it_review_enabled is True
        assert configuration.is_active is False


def test_configuration_version_must_be_unique(
    app: Flask,
    active_user: User,
) -> None:
    """Two configurations cannot use the same version number."""
    with app.app_context():
        db.session.add_all(
            [
                WorkflowConfiguration(
                    version_number=1,
                    name="Version one",
                    created_by_user_id=active_user.id,
                ),
                WorkflowConfiguration(
                    version_number=1,
                    name="Duplicate version",
                    created_by_user_id=active_user.id,
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_low_threshold_must_be_below_high_threshold(
    app: Flask,
    active_user: User,
) -> None:
    """Invalid threshold ordering should be rejected."""
    with app.app_context():
        configuration = WorkflowConfiguration(
            version_number=1,
            name="Invalid thresholds",
            low_value_threshold=Decimal("10000.00"),
            high_value_threshold=Decimal("1000.00"),
            it_review_threshold=Decimal("5000.00"),
            created_by_user_id=active_user.id,
        )

        db.session.add(configuration)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_step_type_must_be_unique_per_configuration(
    app: Flask,
    active_user: User,
) -> None:
    """A configuration cannot contain duplicate step types."""
    with app.app_context():
        configuration = WorkflowConfiguration(
            version_number=1,
            name="Duplicate steps",
            created_by_user_id=active_user.id,
        )

        configuration.step_configurations.extend(
            [
                build_step(
                    step_type=StepType.MANAGER_APPROVAL,
                    role_name=RoleName.MANAGER_APPROVER,
                    sequence_hint=1,
                ),
                build_step(
                    step_type=StepType.MANAGER_APPROVAL,
                    role_name=RoleName.MANAGER_APPROVER,
                    sequence_hint=2,
                ),
            ]
        )

        db.session.add(configuration)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_step_sla_must_be_positive(
    app: Flask,
    active_user: User,
) -> None:
    """A workflow step must have a positive SLA duration."""
    with app.app_context():
        configuration = WorkflowConfiguration(
            version_number=1,
            name="Invalid SLA",
            created_by_user_id=active_user.id,
        )

        configuration.step_configurations.append(
            build_step(
                step_type=StepType.MANAGER_APPROVAL,
                role_name=RoleName.MANAGER_APPROVER,
                sequence_hint=1,
                sla_duration_hours=0,
            )
        )

        db.session.add(configuration)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_service_creates_configuration_with_steps(
    app: Flask,
    active_user: User,
) -> None:
    """The service should create a complete inactive configuration."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        configuration = create_workflow_configuration(
            version_number=1,
            name="Aurevia purchase workflow",
            low_value_threshold=Decimal("1000.00"),
            high_value_threshold=Decimal("10000.00"),
            it_review_threshold=Decimal("5000.00"),
            it_review_enabled=True,
            created_by=stored_user,
            step_configurations=[
                build_step(
                    step_type=StepType.MANAGER_APPROVAL,
                    role_name=RoleName.MANAGER_APPROVER,
                    sequence_hint=1,
                ),
                build_step(
                    step_type=StepType.IT_REVIEW,
                    role_name=RoleName.IT_REVIEWER,
                    sequence_hint=2,
                ),
                build_step(
                    step_type=StepType.FINANCE_APPROVAL,
                    role_name=RoleName.FINANCE_APPROVER,
                    sequence_hint=3,
                ),
                build_step(
                    step_type=StepType.DIRECTOR_APPROVAL,
                    role_name=RoleName.DIRECTOR_APPROVER,
                    sequence_hint=4,
                ),
            ],
        )

        assert configuration.id is not None
        assert configuration.is_active is False
        assert len(configuration.step_configurations) == 4


def test_service_rejects_incorrect_required_role(
    app: Flask,
    active_user: User,
) -> None:
    """A step type should require its matching approval role."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        with pytest.raises(
            WorkflowConfigurationError,
            match="MANAGER_APPROVER",
        ):
            create_workflow_configuration(
                version_number=1,
                name="Invalid role configuration",
                low_value_threshold=Decimal("1000.00"),
                high_value_threshold=Decimal("10000.00"),
                it_review_threshold=Decimal("5000.00"),
                it_review_enabled=True,
                created_by=stored_user,
                step_configurations=[
                    build_step(
                        step_type=StepType.MANAGER_APPROVAL,
                        role_name=RoleName.FINANCE_APPROVER,
                        sequence_hint=1,
                    )
                ],
            )


def test_inactive_default_assignee_is_rejected(
    app: Flask,
    active_user: User,
    inactive_user: User,
) -> None:
    """A default approver must have an active account."""
    assign_role(
        app,
        inactive_user,
        RoleName.FINANCE_APPROVER,
    )

    with app.app_context():
        stored_creator = db.session.get(User, active_user.id)
        stored_assignee = db.session.get(User, inactive_user.id)

        with pytest.raises(
            WorkflowConfigurationError,
            match="must be active",
        ):
            create_workflow_configuration(
                version_number=1,
                name="Inactive assignee configuration",
                low_value_threshold=Decimal("1000.00"),
                high_value_threshold=Decimal("10000.00"),
                it_review_threshold=Decimal("5000.00"),
                it_review_enabled=True,
                created_by=stored_creator,
                step_configurations=[
                    build_step(
                        step_type=StepType.FINANCE_APPROVAL,
                        role_name=RoleName.FINANCE_APPROVER,
                        sequence_hint=1,
                        default_assignee=stored_assignee,
                    )
                ],
            )


def test_activating_configuration_archives_previous_version(
    app: Flask,
    active_user: User,
) -> None:
    """Only the most recently activated configuration should remain active."""
    with app.app_context():
        first = WorkflowConfiguration(
            version_number=1,
            name="Version one",
            created_by_user_id=active_user.id,
            is_active=True,
        )
        second = WorkflowConfiguration(
            version_number=2,
            name="Version two",
            created_by_user_id=active_user.id,
        )

        db.session.add_all([first, second])
        db.session.commit()

        activate_workflow_configuration(second)

        assert first.is_active is False
        assert first.archived_at is not None
        assert second.is_active is True
        assert second.activated_at is not None
        assert second.effective_from is not None

        active_configuration = get_active_workflow_configuration()

        assert active_configuration.id == second.id


def test_missing_active_configuration_raises_controlled_error(
    app: Flask,
) -> None:
    """The service should fail clearly when no active version exists."""
    with app.app_context():
        with pytest.raises(
            WorkflowConfigurationError,
            match="No active workflow configuration",
        ):
            get_active_workflow_configuration()
