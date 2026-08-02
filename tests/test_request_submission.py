"""Tests for request submission and workflow initialization."""

from datetime import date
from decimal import Decimal

import pytest
from app.authorization import RoleName
from app.extensions import db
from app.models import (
    PurchaseRequest,
    RequestCategory,
    RequestRevision,
    RequestStatus,
    Role,
    StepConfiguration,
    StepType,
    User,
    UserRole,
    WorkflowConfiguration,
    WorkflowCycle,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.exceptions import (
    ApproverAssignmentError,
    InvalidTransitionError,
    RequestValidationError,
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
) -> User:
    """Create an active test user."""
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        department_id=department_id,
        is_active=True,
        password_hash="temporary",
    )
    user.set_password("StrongPassword123!")

    db.session.add(user)
    db.session.flush()

    return user


def create_complete_request(
    *,
    requester: User,
    amount: Decimal = Decimal("7200.00"),
    category: RequestCategory = RequestCategory.SOFTWARE,
) -> PurchaseRequest:
    """Create a complete request ready for submission."""
    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=requester.department_id,
        title="Annual software licenses",
        description="Three annual software licenses.",
        business_justification=(
            "The Sales team requires the licenses for client work."
        ),
        category=category,
        supplier="Aurevia Software Partner",
        requested_amount=amount,
        currency="EUR",
        expected_purchase_date=date(2026, 10, 1),
        status=RequestStatus.DRAFT,
    )

    db.session.add(purchase_request)
    db.session.flush()

    return purchase_request


def create_assignment_environment(
    *,
    requester: User,
    department_id: int,
) -> WorkflowConfiguration:
    """Create approvers and an active workflow configuration."""
    manager = create_user(
        email="submission.manager@aurevia.example",
        department_id=department_id,
        first_name="Morgan",
        last_name="Manager",
    )
    it_reviewer = create_user(
        email="submission.it@aurevia.example",
        department_id=department_id,
        first_name="Isaac",
        last_name="Reviewer",
    )
    finance_approver = create_user(
        email="submission.finance@aurevia.example",
        department_id=department_id,
        first_name="Fiona",
        last_name="Finance",
    )
    director = create_user(
        email="submission.director@aurevia.example",
        department_id=department_id,
        first_name="Diana",
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

    configuration = WorkflowConfiguration(
        version_number=1,
        name="Submission test workflow",
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
                required_role_name=(RoleName.MANAGER_APPROVER.value),
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
                required_role_name=(RoleName.FINANCE_APPROVER.value),
                sequence_hint=3,
                default_assignee=finance_approver,
            ),
            StepConfiguration(
                step_type=StepType.DIRECTOR_APPROVAL,
                sla_duration_hours=72,
                required_role_name=(RoleName.DIRECTOR_APPROVER.value),
                sequence_hint=4,
                default_assignee=director,
            ),
        ]
    )

    db.session.add(configuration)
    db.session.flush()

    return configuration


def test_medium_value_it_request_initializes_correct_path(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A EUR 7,200 Software request should create three steps."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )

        workflow_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        assert purchase_request.status == RequestStatus.IN_REVIEW
        assert purchase_request.current_revision_number == 1
        assert purchase_request.submitted_at is not None

        assert workflow_cycle.cycle_number == 1
        assert len(workflow_cycle.steps) == 3

        assert [step.step_type for step in workflow_cycle.steps] == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
        ]


def test_first_step_is_active_and_later_steps_are_pending(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Only Manager Approval should be active after submission."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )

        workflow_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        first_step, second_step, third_step = workflow_cycle.steps

        assert first_step.status == WorkflowStepStatus.ACTIVE
        assert first_step.activated_at is not None
        assert first_step.deadline_at is not None

        assert second_step.status == WorkflowStepStatus.PENDING
        assert second_step.activated_at is None
        assert second_step.deadline_at is None

        assert third_step.status == WorkflowStepStatus.PENDING
        assert third_step.activated_at is None
        assert third_step.deadline_at is None


def test_submission_creates_immutable_revision_snapshot(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Submission should preserve current request values in a revision."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )

        submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        revision = db.session.scalar(
            select(RequestRevision).where(
                RequestRevision.purchase_request_id == purchase_request.id
            )
        )

        assert revision is not None
        assert revision.revision_number == 1
        assert revision.title == purchase_request.title
        assert revision.category == RequestCategory.SOFTWARE
        assert revision.requested_amount == Decimal("7200.00")
        assert revision.submitted_at is not None


def test_low_value_request_creates_manager_step_only(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A request below EUR 1,000 should create one step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        workflow_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        assert len(workflow_cycle.steps) == 1
        assert workflow_cycle.steps[0].step_type == StepType.MANAGER_APPROVAL


def test_high_value_it_request_creates_complete_path(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A high-value IT request should create all four steps."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
            amount=Decimal("18000.00"),
            category=RequestCategory.IT_SERVICES,
        )

        workflow_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        assert [step.step_type for step in workflow_cycle.steps] == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
            StepType.DIRECTOR_APPROVAL,
        ]


def test_incomplete_request_is_rejected_without_workflow(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """An incomplete draft should remain editable."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )
        purchase_request.business_justification = None

        with pytest.raises(
            RequestValidationError,
            match="business justification",
        ):
            submit_purchase_request(
                purchase_request=purchase_request,
                requester=requester,
            )

        assert purchase_request.status == RequestStatus.DRAFT

        cycle_count = db.session.scalar(select(func.count(WorkflowCycle.id)))
        revision_count = db.session.scalar(select(func.count(RequestRevision.id)))

        assert cycle_count == 0
        assert revision_count == 0


def test_cancelled_request_cannot_be_submitted(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """A cancelled request should remain final."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )
        purchase_request.status = RequestStatus.CANCELLED

        with pytest.raises(
            InvalidTransitionError,
            match="draft or returned",
        ):
            submit_purchase_request(
                purchase_request=purchase_request,
                requester=requester,
            )


def test_another_user_cannot_submit_request(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Only the request owner may submit it."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        other_user = create_user(
            email="other.submitter@aurevia.example",
            department_id=department.id,
            first_name="Other",
            last_name="Submitter",
        )

        purchase_request = create_complete_request(
            requester=requester,
        )

        with pytest.raises(
            RequestValidationError,
            match="request owner",
        ):
            submit_purchase_request(
                purchase_request=purchase_request,
                requester=other_user,
            )


def test_assignment_failure_does_not_create_partial_workflow(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Missing assignment must leave the request unchanged."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        configuration = create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        finance_configuration = next(
            step_configuration
            for step_configuration in configuration.step_configurations
            if step_configuration.step_type == StepType.FINANCE_APPROVAL
        )
        finance_configuration.default_assignee = None

        purchase_request = create_complete_request(
            requester=requester,
            amount=Decimal("3000.00"),
            category=RequestCategory.HARDWARE,
        )

        with pytest.raises(
            ApproverAssignmentError,
            match="No default approver",
        ):
            submit_purchase_request(
                purchase_request=purchase_request,
                requester=requester,
            )

        assert purchase_request.status == RequestStatus.DRAFT
        assert purchase_request.current_revision_number == 0

        assert db.session.scalar(select(func.count(RequestRevision.id))) == 0
        assert db.session.scalar(select(func.count(WorkflowCycle.id))) == 0
        assert db.session.scalar(select(func.count(WorkflowStep.id))) == 0


def test_submitted_request_cannot_be_submitted_twice(
    app: Flask,
    active_user: User,
    department,
) -> None:
    """Repeated submission should not create duplicate workflow data."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        create_assignment_environment(
            requester=requester,
            department_id=department.id,
        )

        purchase_request = create_complete_request(
            requester=requester,
        )

        submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        with pytest.raises(
            InvalidTransitionError,
            match="draft or returned",
        ):
            submit_purchase_request(
                purchase_request=purchase_request,
                requester=requester,
            )

        assert db.session.scalar(select(func.count(RequestRevision.id))) == 1
        assert db.session.scalar(select(func.count(WorkflowCycle.id))) == 1
