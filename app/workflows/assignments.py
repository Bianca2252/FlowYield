"""Approver assignment rules for generated workflow steps."""

from dataclasses import dataclass

from app.authorization import RoleName
from app.models import (
    StepConfiguration,
    StepType,
    User,
    WorkflowConfiguration,
)
from app.workflows.exceptions import (
    ApproverAssignmentError,
    InactiveApproverError,
    InvalidApproverRoleError,
    MissingManagerError,
    SelfApprovalError,
)
from app.workflows.rules import ApprovalPathStep

REQUIRED_ROLE_BY_STEP = {
    StepType.MANAGER_APPROVAL: RoleName.MANAGER_APPROVER,
    StepType.IT_REVIEW: RoleName.IT_REVIEWER,
    StepType.FINANCE_APPROVAL: RoleName.FINANCE_APPROVER,
    StepType.DIRECTOR_APPROVAL: RoleName.DIRECTOR_APPROVER,
}


@dataclass(frozen=True, slots=True)
class AssignedApprovalStep:
    """Describe one generated workflow step and its assigned approver."""

    step_type: StepType
    sequence_number: int
    reason_for_inclusion: str
    required_role_name: str
    assigned_user: User
    sla_duration_hours: int


def get_step_configuration(
    *,
    workflow_configuration: WorkflowConfiguration,
    step_type: StepType,
) -> StepConfiguration:
    """Return the configuration matching one generated step."""
    matching_configurations = [
        step_configuration
        for step_configuration in workflow_configuration.step_configurations
        if step_configuration.step_type == step_type and step_configuration.is_enabled
    ]

    if not matching_configurations:
        raise ApproverAssignmentError(
            f"No enabled configuration exists for {step_type.value}."
        )

    if len(matching_configurations) > 1:
        raise ApproverAssignmentError(
            f"Multiple configurations exist for {step_type.value}."
        )

    return matching_configurations[0]


def validate_assignee(
    *,
    requester: User,
    assignee: User,
    step_type: StepType,
) -> None:
    """Validate one proposed workflow approver."""
    required_role = REQUIRED_ROLE_BY_STEP[step_type]

    if assignee.id == requester.id:
        raise SelfApprovalError(f"The requester cannot perform {step_type.value}.")

    if not assignee.is_active:
        raise InactiveApproverError(
            f"The assigned approver for {step_type.value} is inactive."
        )

    if not assignee.has_role(required_role.value):
        raise InvalidApproverRoleError(
            f"The assigned approver for {step_type.value} must hold "
            f"the {required_role.value} role."
        )


def resolve_assignee(
    *,
    requester: User,
    step_type: StepType,
    step_configuration: StepConfiguration,
) -> User:
    """Resolve the approver for one generated workflow step."""
    if step_type == StepType.MANAGER_APPROVAL:
        manager = requester.manager

        if manager is None:
            raise MissingManagerError(
                "The requester does not have a configured manager."
            )

        validate_assignee(
            requester=requester,
            assignee=manager,
            step_type=step_type,
        )

        return manager

    default_assignee = step_configuration.default_assignee

    if default_assignee is None:
        raise ApproverAssignmentError(
            f"No default approver is configured for {step_type.value}."
        )

    validate_assignee(
        requester=requester,
        assignee=default_assignee,
        step_type=step_type,
    )

    return default_assignee


def assign_approval_path(
    *,
    requester: User,
    approval_path: list[ApprovalPathStep],
    workflow_configuration: WorkflowConfiguration,
) -> list[AssignedApprovalStep]:
    """Assign an eligible approver to every generated path step."""
    assigned_steps: list[AssignedApprovalStep] = []

    for path_step in approval_path:
        step_configuration = get_step_configuration(
            workflow_configuration=workflow_configuration,
            step_type=path_step.step_type,
        )

        assignee = resolve_assignee(
            requester=requester,
            step_type=path_step.step_type,
            step_configuration=step_configuration,
        )

        required_role = REQUIRED_ROLE_BY_STEP[path_step.step_type]

        assigned_steps.append(
            AssignedApprovalStep(
                step_type=path_step.step_type,
                sequence_number=path_step.sequence_number,
                reason_for_inclusion=path_step.reason_for_inclusion,
                required_role_name=required_role.value,
                assigned_user=assignee,
                sla_duration_hours=(step_configuration.sla_duration_hours),
            )
        )

    return assigned_steps
