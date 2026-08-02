"""Workflow approval decision service."""

from datetime import UTC, datetime, timedelta

from app.extensions import db
from app.models import (
    ApprovalDecision,
    DecisionType,
    RequestStatus,
    SLAResult,
    User,
    WorkflowCycleStatus,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.exceptions import (
    ApprovalDecisionError,
    DecisionCommentRequiredError,
    InvalidTransitionError,
    SelfApprovalError,
    UnauthorizedDecisionError,
)


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Return a datetime that can safely be compared in UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def validate_decision_comment(
    *,
    decision: DecisionType,
    comment: str | None,
) -> str | None:
    """Validate and normalize the decision comment."""
    normalized_comment = comment.strip() if comment else None

    if (
        decision
        in {
            DecisionType.REJECT,
            DecisionType.RETURN_FOR_CHANGES,
        }
        and not normalized_comment
    ):
        raise DecisionCommentRequiredError(
            "A comment is required when rejecting or returning a request for changes."
        )

    return normalized_comment


def validate_decision_actor(
    *,
    workflow_step: WorkflowStep,
    actor: User,
) -> None:
    """Validate that the actor may decide the active workflow step."""
    workflow_cycle = workflow_step.workflow_cycle
    purchase_request = workflow_cycle.purchase_request

    if workflow_cycle.status != WorkflowCycleStatus.ACTIVE:
        raise InvalidTransitionError(
            "Decisions may only be recorded for an active workflow cycle."
        )

    if workflow_step.status != WorkflowStepStatus.ACTIVE:
        raise InvalidTransitionError(
            "Decisions may only be recorded for the active workflow step."
        )

    if workflow_step.decision is not None:
        raise ApprovalDecisionError("This workflow step already has a decision.")

    if workflow_step.assigned_user_id != actor.id:
        raise UnauthorizedDecisionError(
            "Only the assigned approver may decide this workflow step."
        )

    if not actor.is_active:
        raise UnauthorizedDecisionError(
            "An inactive user cannot record approval decisions."
        )

    if not actor.has_role(workflow_step.required_role_name):
        raise UnauthorizedDecisionError(
            "The assigned user no longer holds the required approval role."
        )

    if purchase_request.requester_id == actor.id:
        raise SelfApprovalError(
            "The requester cannot approve their own purchase request."
        )


def complete_step_sla(
    *,
    workflow_step: WorkflowStep,
    completed_at: datetime,
) -> None:
    """Store the final SLA result for a completed workflow step."""
    if workflow_step.deadline_at is None:
        raise ApprovalDecisionError(
            "The active workflow step does not have an SLA deadline."
        )

    completed_utc = as_utc(completed_at)
    deadline_utc = as_utc(workflow_step.deadline_at)

    if completed_utc <= deadline_utc:
        workflow_step.sla_result = SLAResult.COMPLETED_ON_TIME
        workflow_step.overdue_seconds = 0
        return

    overdue_duration = completed_utc - deadline_utc

    workflow_step.sla_result = SLAResult.COMPLETED_LATE
    workflow_step.overdue_seconds = max(
        int(overdue_duration.total_seconds()),
        0,
    )


def find_next_pending_step(
    workflow_step: WorkflowStep,
) -> WorkflowStep | None:
    """Return the next pending step in the workflow cycle."""
    return next(
        (
            candidate_step
            for candidate_step in workflow_step.workflow_cycle.steps
            if (
                candidate_step.sequence_number > workflow_step.sequence_number
                and candidate_step.status == WorkflowStepStatus.PENDING
            )
        ),
        None,
    )


def activate_step(
    *,
    workflow_step: WorkflowStep,
    activated_at: datetime,
) -> None:
    """Activate a pending workflow step and calculate its deadline."""
    workflow_step.status = WorkflowStepStatus.ACTIVE
    workflow_step.activated_at = activated_at
    workflow_step.deadline_at = activated_at + timedelta(
        hours=workflow_step.sla_duration_hours
    )


def close_remaining_steps(
    *,
    workflow_step: WorkflowStep,
    status: WorkflowStepStatus,
    completed_at: datetime,
) -> None:
    """Close all remaining pending steps after a terminal decision."""
    for remaining_step in workflow_step.workflow_cycle.steps:
        if (
            remaining_step.sequence_number > workflow_step.sequence_number
            and remaining_step.status == WorkflowStepStatus.PENDING
        ):
            remaining_step.status = status
            remaining_step.completed_at = completed_at


def apply_approval(
    *,
    workflow_step: WorkflowStep,
    decided_at: datetime,
) -> None:
    """Approve a step and activate the next one or finish the workflow."""
    workflow_cycle = workflow_step.workflow_cycle
    purchase_request = workflow_cycle.purchase_request

    workflow_step.status = WorkflowStepStatus.APPROVED
    workflow_step.completed_at = decided_at

    next_step = find_next_pending_step(workflow_step)

    if next_step is not None:
        activate_step(
            workflow_step=next_step,
            activated_at=decided_at,
        )
        return

    workflow_cycle.status = WorkflowCycleStatus.APPROVED
    workflow_cycle.completed_at = decided_at

    purchase_request.status = RequestStatus.APPROVED
    purchase_request.completed_at = decided_at


def apply_rejection(
    *,
    workflow_step: WorkflowStep,
    decided_at: datetime,
) -> None:
    """Reject a step and terminate the current request workflow."""
    workflow_cycle = workflow_step.workflow_cycle
    purchase_request = workflow_cycle.purchase_request

    workflow_step.status = WorkflowStepStatus.REJECTED
    workflow_step.completed_at = decided_at

    close_remaining_steps(
        workflow_step=workflow_step,
        status=WorkflowStepStatus.SKIPPED,
        completed_at=decided_at,
    )

    workflow_cycle.status = WorkflowCycleStatus.REJECTED
    workflow_cycle.completed_at = decided_at

    purchase_request.status = RequestStatus.REJECTED
    purchase_request.completed_at = decided_at


def apply_return_for_changes(
    *,
    workflow_step: WorkflowStep,
    decided_at: datetime,
) -> None:
    """Return a request to its owner for a new revision."""
    workflow_cycle = workflow_step.workflow_cycle
    purchase_request = workflow_cycle.purchase_request

    workflow_step.status = WorkflowStepStatus.CHANGES_REQUESTED
    workflow_step.completed_at = decided_at

    close_remaining_steps(
        workflow_step=workflow_step,
        status=WorkflowStepStatus.CANCELLED,
        completed_at=decided_at,
    )

    workflow_cycle.status = WorkflowCycleStatus.CHANGES_REQUESTED
    workflow_cycle.completed_at = decided_at

    purchase_request.status = RequestStatus.CHANGES_REQUESTED
    purchase_request.completed_at = None


def record_approval_decision(
    *,
    workflow_step: WorkflowStep,
    actor: User,
    decision: DecisionType,
    comment: str | None = None,
    decided_at: datetime | None = None,
) -> ApprovalDecision:
    """Record one authoritative workflow decision atomically."""
    validate_decision_actor(
        workflow_step=workflow_step,
        actor=actor,
    )

    normalized_comment = validate_decision_comment(
        decision=decision,
        comment=comment,
    )

    effective_decided_at = decided_at or utc_now()

    approval_decision = ApprovalDecision(
        workflow_step_id=workflow_step.id,
        workflow_cycle_id=workflow_step.workflow_cycle_id,
        purchase_request_id=(workflow_step.workflow_cycle.purchase_request_id),
        actor_id=actor.id,
        decision=decision,
        comment=normalized_comment,
        decided_at=effective_decided_at,
    )

    try:
        db.session.add(approval_decision)
        db.session.flush()

        complete_step_sla(
            workflow_step=workflow_step,
            completed_at=effective_decided_at,
        )

        if decision == DecisionType.APPROVE:
            apply_approval(
                workflow_step=workflow_step,
                decided_at=effective_decided_at,
            )
        elif decision == DecisionType.REJECT:
            apply_rejection(
                workflow_step=workflow_step,
                decided_at=effective_decided_at,
            )
        elif decision == DecisionType.RETURN_FOR_CHANGES:
            apply_return_for_changes(
                workflow_step=workflow_step,
                decided_at=effective_decided_at,
            )
        else:
            raise ApprovalDecisionError(
                "The requested approval decision is not supported."
            )

        db.session.commit()

        return approval_decision

    except Exception:
        db.session.rollback()
        raise
