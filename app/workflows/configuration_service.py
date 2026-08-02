"""Workflow configuration application service."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.authorization import RoleName
from app.extensions import db
from app.models import (
    StepConfiguration,
    StepType,
    User,
    WorkflowConfiguration,
)
from app.workflows.exceptions import WorkflowConfigurationError

EXPECTED_ROLES_BY_STEP = {
    StepType.MANAGER_APPROVAL: RoleName.MANAGER_APPROVER,
    StepType.IT_REVIEW: RoleName.IT_REVIEWER,
    StepType.FINANCE_APPROVAL: RoleName.FINANCE_APPROVER,
    StepType.DIRECTOR_APPROVAL: RoleName.DIRECTOR_APPROVER,
}


def validate_thresholds(
    low_value_threshold: Decimal,
    high_value_threshold: Decimal,
    it_review_threshold: Decimal,
) -> None:
    """Validate monetary workflow thresholds."""
    if low_value_threshold <= 0:
        raise WorkflowConfigurationError(
            "The low-value threshold must be greater than zero."
        )

    if high_value_threshold <= 0:
        raise WorkflowConfigurationError(
            "The high-value threshold must be greater than zero."
        )

    if it_review_threshold <= 0:
        raise WorkflowConfigurationError(
            "The IT Review threshold must be greater than zero."
        )

    if low_value_threshold >= high_value_threshold:
        raise WorkflowConfigurationError(
            "The low-value threshold must be lower than the high-value threshold."
        )


def validate_step_configuration(
    step_configuration: StepConfiguration,
) -> None:
    """Validate one workflow step configuration."""
    if step_configuration.sla_duration_hours <= 0:
        raise WorkflowConfigurationError("SLA duration must be greater than zero.")

    if step_configuration.sequence_hint <= 0:
        raise WorkflowConfigurationError("The step sequence must be greater than zero.")

    expected_role = EXPECTED_ROLES_BY_STEP[step_configuration.step_type]

    if step_configuration.required_role_name != expected_role.value:
        raise WorkflowConfigurationError(
            f"{step_configuration.step_type.value} requires "
            f"the {expected_role.value} role."
        )

    assignee = step_configuration.default_assignee

    if assignee is None:
        return

    if not assignee.is_active:
        raise WorkflowConfigurationError("The default assignee must be active.")

    if not assignee.has_role(expected_role.value):
        raise WorkflowConfigurationError(
            "The default assignee does not hold the required role."
        )


def create_workflow_configuration(
    *,
    version_number: int,
    name: str,
    low_value_threshold: Decimal,
    high_value_threshold: Decimal,
    it_review_threshold: Decimal,
    it_review_enabled: bool,
    created_by: User,
    step_configurations: list[StepConfiguration],
) -> WorkflowConfiguration:
    """Create and persist an inactive workflow configuration version."""
    validate_thresholds(
        low_value_threshold,
        high_value_threshold,
        it_review_threshold,
    )

    if version_number <= 0:
        raise WorkflowConfigurationError(
            "The version number must be greater than zero."
        )

    existing_version = db.session.scalar(
        select(WorkflowConfiguration).where(
            WorkflowConfiguration.version_number == version_number
        )
    )

    if existing_version is not None:
        raise WorkflowConfigurationError(
            "The workflow configuration version already exists."
        )

    step_types = [
        step_configuration.step_type for step_configuration in step_configurations
    ]

    if len(step_types) != len(set(step_types)):
        raise WorkflowConfigurationError(
            "Each workflow step type may be configured only once."
        )

    for step_configuration in step_configurations:
        validate_step_configuration(step_configuration)

    workflow_configuration = WorkflowConfiguration(
        version_number=version_number,
        name=name.strip(),
        low_value_threshold=low_value_threshold,
        high_value_threshold=high_value_threshold,
        it_review_threshold=it_review_threshold,
        it_review_enabled=it_review_enabled,
        created_by_user_id=created_by.id,
        is_active=False,
    )

    workflow_configuration.step_configurations.extend(step_configurations)

    db.session.add(workflow_configuration)
    db.session.commit()

    return workflow_configuration


def activate_workflow_configuration(
    workflow_configuration: WorkflowConfiguration,
) -> WorkflowConfiguration:
    """Activate one configuration and archive the previous version."""
    activation_time = datetime.now(UTC)

    active_configurations = db.session.scalars(
        select(WorkflowConfiguration).where(
            WorkflowConfiguration.is_active.is_(True),
            WorkflowConfiguration.id != workflow_configuration.id,
        )
    ).all()

    for active_configuration in active_configurations:
        active_configuration.is_active = False
        active_configuration.archived_at = activation_time

    workflow_configuration.is_active = True
    workflow_configuration.activated_at = activation_time
    workflow_configuration.effective_from = activation_time
    workflow_configuration.archived_at = None

    db.session.commit()

    return workflow_configuration


def get_active_workflow_configuration() -> WorkflowConfiguration:
    """Return the active workflow configuration."""
    active_configurations = db.session.scalars(
        select(WorkflowConfiguration).where(WorkflowConfiguration.is_active.is_(True))
    ).all()

    if not active_configurations:
        raise WorkflowConfigurationError("No active workflow configuration exists.")

    if len(active_configurations) > 1:
        raise WorkflowConfigurationError(
            "Multiple active workflow configurations were found."
        )

    return active_configurations[0]
