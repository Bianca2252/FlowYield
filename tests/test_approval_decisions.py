"""Tests for workflow approval decisions."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from app.authorization import RoleName
from app.extensions import db
from app.models import (
    ApprovalDecision,
    DecisionType,
    Department,
    PurchaseRequest,
    RequestCategory,
    RequestStatus,
    Role,
    StepConfiguration,
    StepType,
    User,
    UserRole,
    WorkflowConfiguration,
    WorkflowCycleStatus,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.decision_service import record_approval_decision
from app.workflows.exceptions import (
    DecisionCommentRequiredError,
    InvalidTransitionError,
    SelfApprovalError,
    UnauthorizedDecisionError,
)
from app.workflows.submission_service import submit_purchase_request
from flask import Flask
from sqlalchemy import func, select


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
    """Assign one role to a user."""
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
        db.session.flush()


def create_user(
    *,
    email: str,
    department: Department,
    first_name: str,
    last_name: str,
) -> User:
    """Create an active workflow user."""
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        department_id=department.id,
        password_hash="temporary",
        is_active=True,
    )
    user.set_password("StrongPassword123!")

    db.session.add(user)
    db.session.flush()

    return user


def create_active_workflow(
    *,
    requester: User,
    department: Department,
    amount: Decimal = Decimal("7200.00"),
    category: RequestCategory = RequestCategory.SOFTWARE,
) -> tuple[PurchaseRequest, list[WorkflowStep]]:
    """Create and submit a request with valid approver assignments."""
    manager = create_user(
        email="decision.manager@aurevia.example",
        department=department,
        first_name="Morgan",
        last_name="Manager",
    )
    it_reviewer = create_user(
        email="decision.it@aurevia.example",
        department=department,
        first_name="Isaac",
        last_name="Reviewer",
    )
    finance_approver = create_user(
        email="decision.finance@aurevia.example",
        department=department,
        first_name="Fiona",
        last_name="Finance",
    )
    director = create_user(
        email="decision.director@aurevia.example",
        department=department,
        first_name="Diana",
        last_name="Director",
    )

    assign_role(manager, RoleName.MANAGER_APPROVER)
    assign_role(it_reviewer, RoleName.IT_REVIEWER)
    assign_role(finance_approver, RoleName.FINANCE_APPROVER)
    assign_role(director, RoleName.DIRECTOR_APPROVER)

    requester.manager = manager

    configuration = WorkflowConfiguration(
        version_number=1,
        name="Approval decision test workflow",
        low_value_threshold=Decimal("1000.00"),
        high_value_threshold=Decimal("10000.00"),
        it_review_threshold=Decimal("5000.00"),
        it_review_enabled=True,
        is_active=True,
        created_by_user_id=requester.id,
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
                default_assignee=director,
            ),
        ]
    )

    db.session.add(configuration)
    db.session.flush()

    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=department.id,
        title="Decision test request",
        description="A complete request used for workflow decisions.",
        business_justification="Required for operational delivery.",
        category=category,
        supplier="Decision Test Supplier",
        requested_amount=amount,
        currency="EUR",
        expected_purchase_date=date(2026, 10, 1),
        status=RequestStatus.DRAFT,
    )

    db.session.add(purchase_request)
    db.session.flush()

    workflow_cycle = submit_purchase_request(
        purchase_request=purchase_request,
        requester=requester,
    )

    return purchase_request, list(workflow_cycle.steps)


def test_approval_activates_next_pending_step(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Approving Manager should activate IT Review."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, steps = create_active_workflow(
            requester=requester,
            department=department,
        )

        manager_step, it_step, finance_step = steps

        decision = record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.APPROVE,
        )

        assert decision.decision == DecisionType.APPROVE
        assert manager_step.status == WorkflowStepStatus.APPROVED
        assert manager_step.completed_at is not None
        assert it_step.status == WorkflowStepStatus.ACTIVE
        assert it_step.activated_at is not None
        assert it_step.deadline_at is not None
        assert finance_step.status == WorkflowStepStatus.PENDING
        assert purchase_request.status == RequestStatus.IN_REVIEW


def test_final_approval_completes_request_and_cycle(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Approving the final step should approve the request."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.APPROVE,
        )

        assert purchase_request.status == RequestStatus.APPROVED
        assert purchase_request.completed_at is not None
        assert manager_step.workflow_cycle.status == WorkflowCycleStatus.APPROVED
        assert manager_step.workflow_cycle.completed_at is not None


def test_rejection_terminates_workflow_and_skips_future_steps(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Rejecting an active step should terminate the workflow."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, steps = create_active_workflow(
            requester=requester,
            department=department,
        )

        manager_step, it_step, finance_step = steps

        record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.REJECT,
            comment="The business justification is insufficient.",
        )

        assert manager_step.status == WorkflowStepStatus.REJECTED
        assert it_step.status == WorkflowStepStatus.SKIPPED
        assert finance_step.status == WorkflowStepStatus.SKIPPED
        assert purchase_request.status == RequestStatus.REJECTED
        assert purchase_request.completed_at is not None
        assert manager_step.workflow_cycle.status == WorkflowCycleStatus.REJECTED


def test_return_for_changes_returns_request_to_owner(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Returning a request should make it editable again."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, steps = create_active_workflow(
            requester=requester,
            department=department,
        )

        manager_step, it_step, finance_step = steps

        record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.RETURN_FOR_CHANGES,
            comment="Add a more detailed cost breakdown.",
        )

        assert manager_step.status == WorkflowStepStatus.CHANGES_REQUESTED
        assert it_step.status == WorkflowStepStatus.CANCELLED
        assert finance_step.status == WorkflowStepStatus.CANCELLED
        assert purchase_request.status == RequestStatus.CHANGES_REQUESTED
        assert purchase_request.completed_at is None
        assert (
            manager_step.workflow_cycle.status == WorkflowCycleStatus.CHANGES_REQUESTED
        )


@pytest.mark.parametrize(
    "decision",
    [
        DecisionType.REJECT,
        DecisionType.RETURN_FOR_CHANGES,
    ],
)
def test_negative_decision_requires_comment(
    app: Flask,
    active_user: User,
    department: Department,
    decision: DecisionType,
) -> None:
    """Reject and return-for-changes require an explanation."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        with pytest.raises(
            DecisionCommentRequiredError,
            match="comment is required",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=manager_step.assigned_user,
                decision=decision,
                comment="   ",
            )

        assert manager_step.status == WorkflowStepStatus.ACTIVE
        assert manager_step.decision is None


def test_unassigned_user_cannot_decide_step(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A different approver should not decide the active step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        outsider = create_user(
            email="decision.outsider@aurevia.example",
            department=department,
            first_name="Una",
            last_name="Assigned",
        )
        assign_role(outsider, RoleName.MANAGER_APPROVER)

        with pytest.raises(
            UnauthorizedDecisionError,
            match="assigned approver",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=outsider,
                decision=DecisionType.APPROVE,
            )


def test_inactive_assignee_cannot_decide_step(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Inactive approvers should be blocked at decision time."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]
        manager_step.assigned_user.is_active = False

        with pytest.raises(
            UnauthorizedDecisionError,
            match="inactive user",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=manager_step.assigned_user,
                decision=DecisionType.APPROVE,
            )


def test_assignee_without_required_role_cannot_decide(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Role removal should immediately block approval authority."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]
        manager_step.assigned_user.role_assignments.clear()
        db.session.flush()

        with pytest.raises(
            UnauthorizedDecisionError,
            match="required approval role",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=manager_step.assigned_user,
                decision=DecisionType.APPROVE,
            )


def test_requester_self_approval_is_rejected(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A requester must never approve their own request."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        assign_role(requester, RoleName.MANAGER_APPROVER)
        manager_step.assigned_user = requester
        db.session.flush()

        with pytest.raises(
            SelfApprovalError,
            match="own purchase request",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=requester,
                decision=DecisionType.APPROVE,
            )


def test_completed_step_cannot_receive_second_decision(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """One workflow step should have one authoritative decision."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]
        actor = manager_step.assigned_user

        record_approval_decision(
            workflow_step=manager_step,
            actor=actor,
            decision=DecisionType.APPROVE,
        )

        with pytest.raises(
            InvalidTransitionError,
            match="active workflow cycle",
        ):
            record_approval_decision(
                workflow_step=manager_step,
                actor=actor,
                decision=DecisionType.APPROVE,
            )

        decision_count = db.session.scalar(select(func.count(ApprovalDecision.id)))

        assert decision_count == 1


def test_late_decision_records_completed_late_sla(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A decision after deadline should record overdue duration."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        manager_step.deadline_at = datetime.now(UTC) - timedelta(hours=2)
        decided_at = datetime.now(UTC)

        record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.APPROVE,
            decided_at=decided_at,
        )

        assert manager_step.sla_result.value == "COMPLETED_LATE"
        assert manager_step.overdue_seconds is not None
        assert manager_step.overdue_seconds >= 7199


def test_on_time_decision_records_completed_on_time_sla(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A decision before deadline should satisfy the SLA."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, steps = create_active_workflow(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        manager_step = steps[0]

        record_approval_decision(
            workflow_step=manager_step,
            actor=manager_step.assigned_user,
            decision=DecisionType.APPROVE,
        )

        assert manager_step.sla_result.value == "COMPLETED_ON_TIME"
        assert manager_step.overdue_seconds == 0
