"""Tests for workflow execution models."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.authorization import RoleName
from app.extensions import db
from app.models import (
    ApprovalDecision,
    DecisionType,
    PurchaseRequest,
    RequestCategory,
    RequestRevision,
    Role,
    StepType,
    User,
    UserRole,
    WorkflowConfiguration,
    WorkflowCycle,
    WorkflowCycleStatus,
    WorkflowStep,
    WorkflowStepStatus,
)
from flask import Flask
from sqlalchemy.exc import IntegrityError


def assign_role(
    user: User,
    role_name: RoleName,
) -> None:
    """Assign a role to a user in the current database session."""
    role = Role(name=role_name.value)

    db.session.add(role)
    db.session.flush()

    db.session.add(
        UserRole(
            user=user,
            role=role,
        )
    )
    db.session.flush()


def create_revision(
    *,
    requester: User,
    purchase_request: PurchaseRequest,
) -> RequestRevision:
    """Create a submitted request revision."""
    revision = RequestRevision(
        purchase_request=purchase_request,
        revision_number=1,
        title="Development laptops",
        description="Purchase laptops for the engineering team.",
        business_justification="Existing hardware is obsolete.",
        category=RequestCategory.HARDWARE,
        supplier="Aurevia Hardware Partner",
        requested_amount=Decimal("4500.00"),
        currency="EUR",
        department_id=requester.department_id,
        submitted_by_user_id=requester.id,
    )

    db.session.add(revision)
    db.session.flush()

    return revision


def create_configuration(
    creator: User,
) -> WorkflowConfiguration:
    """Create a workflow configuration for model tests."""
    configuration = WorkflowConfiguration(
        version_number=1,
        name="Default workflow",
        created_by_user_id=creator.id,
        is_active=True,
    )

    db.session.add(configuration)
    db.session.flush()

    return configuration


def create_cycle(
    *,
    requester: User,
    purchase_request: PurchaseRequest,
    revision: RequestRevision,
    configuration: WorkflowConfiguration,
    cycle_number: int = 1,
) -> WorkflowCycle:
    """Create a workflow cycle."""
    cycle = WorkflowCycle(
        purchase_request_id=purchase_request.id,
        request_revision_id=revision.id,
        workflow_configuration_id=configuration.id,
        cycle_number=cycle_number,
    )

    db.session.add(cycle)
    db.session.flush()

    return cycle


def create_step(
    *,
    cycle: WorkflowCycle,
    assignee: User,
    sequence_number: int = 1,
    status: WorkflowStepStatus = WorkflowStepStatus.ACTIVE,
) -> WorkflowStep:
    """Create a workflow step."""
    step = WorkflowStep(
        workflow_cycle=cycle,
        step_type=StepType.MANAGER_APPROVAL,
        sequence_number=sequence_number,
        required_role_name=RoleName.MANAGER_APPROVER.value,
        assigned_user_id=assignee.id,
        status=status,
        reason_for_inclusion=("Manager Approval is required for every request."),
        activated_at=(
            datetime.now(UTC) if status == WorkflowStepStatus.ACTIVE else None
        ),
        deadline_at=(
            datetime.now(UTC) + timedelta(hours=24)
            if status == WorkflowStepStatus.ACTIVE
            else None
        ),
        sla_duration_hours=24,
    )

    db.session.add(step)
    db.session.flush()

    return step


def prepare_workflow(
    active_user: User,
    department_id: int,
) -> tuple[
    PurchaseRequest,
    RequestRevision,
    WorkflowConfiguration,
]:
    """Create the shared request, revision, and configuration."""
    purchase_request = PurchaseRequest(
        requester_id=active_user.id,
        department_id=department_id,
        title="Development laptops",
        requested_amount=Decimal("4500.00"),
        category=RequestCategory.HARDWARE,
    )

    db.session.add(purchase_request)
    db.session.flush()

    revision = create_revision(
        requester=active_user,
        purchase_request=purchase_request,
    )
    configuration = create_configuration(active_user)

    return purchase_request, revision, configuration


def test_workflow_cycle_defaults(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A new workflow cycle should begin as active."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        request, revision, configuration = prepare_workflow(
            stored_user,
            department.id,
        )

        cycle = create_cycle(
            requester=stored_user,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        db.session.commit()

        assert cycle.id is not None
        assert cycle.status == WorkflowCycleStatus.ACTIVE
        assert cycle.cycle_number == 1
        assert cycle.request_revision == revision
        assert cycle.purchase_request == request


def test_cycle_number_must_be_unique_per_request(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A request cannot contain duplicate workflow cycle numbers."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        request, revision, configuration = prepare_workflow(
            stored_user,
            department.id,
        )

        second_revision = RequestRevision(
            purchase_request=request,
            revision_number=2,
            title="Updated laptops",
            description="Updated laptop purchase.",
            business_justification="Updated business need.",
            category=RequestCategory.HARDWARE,
            requested_amount=Decimal("5000.00"),
            currency="EUR",
            department_id=stored_user.department_id,
            submitted_by_user_id=stored_user.id,
        )

        db.session.add(second_revision)
        db.session.flush()

        db.session.add_all(
            [
                WorkflowCycle(
                    purchase_request_id=request.id,
                    request_revision_id=revision.id,
                    workflow_configuration_id=configuration.id,
                    cycle_number=1,
                ),
                WorkflowCycle(
                    purchase_request_id=request.id,
                    request_revision_id=second_revision.id,
                    workflow_configuration_id=configuration.id,
                    cycle_number=1,
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_revision_can_have_only_one_workflow_cycle(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """One submitted revision should map to one workflow cycle."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)

        request, revision, configuration = prepare_workflow(
            stored_user,
            department.id,
        )

        db.session.add_all(
            [
                WorkflowCycle(
                    purchase_request_id=request.id,
                    request_revision_id=revision.id,
                    workflow_configuration_id=configuration.id,
                    cycle_number=1,
                ),
                WorkflowCycle(
                    purchase_request_id=request.id,
                    request_revision_id=revision.id,
                    workflow_configuration_id=configuration.id,
                    cycle_number=2,
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_step_sequence_must_be_unique_per_cycle(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
) -> None:
    """A workflow cycle cannot contain duplicate step sequences."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        db.session.add_all(
            [
                WorkflowStep(
                    workflow_cycle=cycle,
                    step_type=StepType.MANAGER_APPROVAL,
                    sequence_number=1,
                    required_role_name=RoleName.MANAGER_APPROVER.value,
                    assigned_user_id=approver.id,
                    status=WorkflowStepStatus.ACTIVE,
                    reason_for_inclusion="Required manager review.",
                    sla_duration_hours=24,
                ),
                WorkflowStep(
                    workflow_cycle=cycle,
                    step_type=StepType.FINANCE_APPROVAL,
                    sequence_number=1,
                    required_role_name=RoleName.FINANCE_APPROVER.value,
                    assigned_user_id=approver.id,
                    status=WorkflowStepStatus.PENDING,
                    reason_for_inclusion="Amount requires Finance review.",
                    sla_duration_hours=24,
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_workflow_cycle_returns_active_step(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
) -> None:
    """The cycle should expose its one active step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        active_step = create_step(
            cycle=cycle,
            assignee=approver,
            sequence_number=1,
        )

        create_step(
            cycle=cycle,
            assignee=approver,
            sequence_number=2,
            status=WorkflowStepStatus.PENDING,
        )

        db.session.commit()

        assert cycle.active_step == active_step
        assert active_step.is_actionable is True


def test_pending_step_is_not_actionable(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
) -> None:
    """A pending workflow step should not accept a decision."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        step = create_step(
            cycle=cycle,
            assignee=approver,
            status=WorkflowStepStatus.PENDING,
        )

        assert step.is_actionable is False


def test_approval_decision_can_be_created(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
) -> None:
    """An active step should support one authoritative approval."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        assign_role(
            approver,
            RoleName.MANAGER_APPROVER,
        )

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        step = create_step(
            cycle=cycle,
            assignee=approver,
        )

        decision = ApprovalDecision(
            workflow_step=step,
            workflow_cycle=cycle,
            purchase_request=request,
            actor=approver,
            decision=DecisionType.APPROVE,
        )

        db.session.add(decision)
        db.session.commit()

        assert decision.id is not None
        assert decision.workflow_step == step
        assert decision.actor == approver
        assert decision.decision == DecisionType.APPROVE
        assert step.decision == decision
        assert step.is_actionable is False


def test_workflow_step_accepts_only_one_decision(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
) -> None:
    """A completed workflow step cannot receive duplicate decisions."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        step = create_step(
            cycle=cycle,
            assignee=approver,
        )

        db.session.add_all(
            [
                ApprovalDecision(
                    workflow_step_id=step.id,
                    workflow_cycle_id=cycle.id,
                    purchase_request_id=request.id,
                    actor_id=approver.id,
                    decision=DecisionType.APPROVE,
                ),
                ApprovalDecision(
                    workflow_step_id=step.id,
                    workflow_cycle_id=cycle.id,
                    purchase_request_id=request.id,
                    actor_id=approver.id,
                    decision=DecisionType.APPROVE,
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


@pytest.mark.parametrize(
    "decision_type",
    [
        DecisionType.REJECT,
        DecisionType.RETURN_FOR_CHANGES,
    ],
)
def test_reject_and_return_decisions_require_comment(
    app: Flask,
    active_user: User,
    inactive_user: User,
    department,
    decision_type: DecisionType,
) -> None:
    """Negative workflow decisions should require a reason."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)
        approver = db.session.get(User, inactive_user.id)
        approver.is_active = True

        request, revision, configuration = prepare_workflow(
            requester,
            department.id,
        )

        cycle = create_cycle(
            requester=requester,
            purchase_request=request,
            revision=revision,
            configuration=configuration,
        )

        step = create_step(
            cycle=cycle,
            assignee=approver,
        )

        decision = ApprovalDecision(
            workflow_step_id=step.id,
            workflow_cycle_id=cycle.id,
            purchase_request_id=request.id,
            actor_id=approver.id,
            decision=decision_type,
            comment=None,
        )

        db.session.add(decision)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
