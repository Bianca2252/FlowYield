"""Tests for returned purchase request resubmission."""

from datetime import date
from decimal import Decimal

from app.authorization import RoleName
from app.extensions import db
from app.models import (
    DecisionType,
    Department,
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
    WorkflowCycleStatus,
    WorkflowStepStatus,
)
from app.workflows.decision_service import (
    record_approval_decision,
)
from app.workflows.submission_service import (
    submit_purchase_request,
)
from flask import Flask
from flask.testing import FlaskClient
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
    """Assign one application role to a user."""
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


def create_resubmission_environment(
    *,
    requester: User,
    department: Department,
) -> PurchaseRequest:
    """Create and submit a request ready to be returned."""
    assign_role(
        requester,
        RoleName.REQUESTER,
    )

    manager = create_user(
        email="resubmit.manager@aurevia.example",
        department=department,
        first_name="Morgan",
        last_name="Manager",
    )
    it_reviewer = create_user(
        email="resubmit.it@aurevia.example",
        department=department,
        first_name="Isaac",
        last_name="Reviewer",
    )
    finance_approver = create_user(
        email="resubmit.finance@aurevia.example",
        department=department,
        first_name="Fiona",
        last_name="Finance",
    )
    director = create_user(
        email="resubmit.director@aurevia.example",
        department=department,
        first_name="Diana",
        last_name="Director",
    )

    assign_role(
        manager,
        RoleName.MANAGER_APPROVER,
    )
    assign_role(
        it_reviewer,
        RoleName.IT_REVIEWER,
    )
    assign_role(
        finance_approver,
        RoleName.FINANCE_APPROVER,
    )
    assign_role(
        director,
        RoleName.DIRECTOR_APPROVER,
    )

    requester.manager = manager

    configuration = WorkflowConfiguration(
        version_number=1,
        name="Resubmission test workflow",
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
                required_role_name=(RoleName.IT_REVIEWER.value),
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

    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=department.id,
        title="Initial software request",
        description="Initial software request description.",
        business_justification=("Initial business justification."),
        category=RequestCategory.SOFTWARE,
        supplier="Initial Supplier",
        requested_amount=Decimal("7200.00"),
        currency="EUR",
        expected_purchase_date=date(2026, 10, 1),
        status=RequestStatus.DRAFT,
    )

    db.session.add(purchase_request)
    db.session.flush()

    first_cycle = submit_purchase_request(
        purchase_request=purchase_request,
        requester=requester,
    )

    manager_step = first_cycle.steps[0]

    record_approval_decision(
        workflow_step=manager_step,
        actor=manager,
        decision=DecisionType.RETURN_FOR_CHANGES,
        comment="Please reduce the cost and clarify the supplier.",
    )

    return purchase_request


def test_returned_request_can_be_edited_through_ui(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """The owner should edit a returned request."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        purchase_request = create_resubmission_environment(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(
        client,
        active_user,
    )

    response = client.post(
        f"/requests/{request_id}/edit",
        data={
            "title": "Revised hardware request",
            "description": ("Revised request with a reduced scope."),
            "business_justification": (
                "Updated justification with detailed cost savings."
            ),
            "category": RequestCategory.HARDWARE.value,
            "supplier": "Revised Supplier",
            "requested_amount": "950.00",
            "expected_purchase_date": "2026-11-01",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert stored_request is not None
        assert stored_request.status == RequestStatus.CHANGES_REQUESTED
        assert stored_request.title == "Revised hardware request"
        assert stored_request.requested_amount == Decimal("950.00")


def test_resubmission_creates_second_revision_and_cycle(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Resubmission should create revision two and cycle two."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        purchase_request = create_resubmission_environment(
            requester=requester,
            department=department,
        )

        purchase_request.title = "Revised request"
        purchase_request.description = "Revised description."
        purchase_request.business_justification = "Revised business justification."
        purchase_request.category = RequestCategory.HARDWARE
        purchase_request.requested_amount = Decimal("950.00")
        purchase_request.supplier = "Revised Supplier"

        second_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        assert purchase_request.current_revision_number == 2
        assert purchase_request.status == RequestStatus.IN_REVIEW
        assert second_cycle.cycle_number == 2

        revisions = list(
            db.session.scalars(
                select(RequestRevision)
                .where(RequestRevision.purchase_request_id == purchase_request.id)
                .order_by(RequestRevision.revision_number)
            ).all()
        )

        cycles = list(
            db.session.scalars(
                select(WorkflowCycle)
                .where(WorkflowCycle.purchase_request_id == purchase_request.id)
                .order_by(WorkflowCycle.cycle_number)
            ).all()
        )

        assert len(revisions) == 2
        assert len(cycles) == 2

        assert revisions[0].title == "Initial software request"
        assert revisions[0].requested_amount == Decimal("7200.00")

        assert revisions[1].title == "Revised request"
        assert revisions[1].requested_amount == Decimal("950.00")


def test_resubmission_preserves_first_cycle_history(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """The returned cycle should remain unchanged in history."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        purchase_request = create_resubmission_environment(
            requester=requester,
            department=department,
        )

        first_cycle = db.session.scalar(
            select(WorkflowCycle).where(
                WorkflowCycle.purchase_request_id == purchase_request.id,
                WorkflowCycle.cycle_number == 1,
            )
        )

        assert first_cycle is not None
        first_decision_count = len(first_cycle.decisions)

        purchase_request.title = "Revised request"
        purchase_request.requested_amount = Decimal("950.00")
        purchase_request.category = RequestCategory.HARDWARE

        submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        db.session.refresh(first_cycle)

        assert first_cycle.status == WorkflowCycleStatus.CHANGES_REQUESTED
        assert first_cycle.completed_at is not None
        assert len(first_cycle.decisions) == first_decision_count
        assert first_cycle.steps[0].status == WorkflowStepStatus.CHANGES_REQUESTED


def test_resubmission_recalculates_approval_path(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A changed amount and category should produce a new path."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        purchase_request = create_resubmission_environment(
            requester=requester,
            department=department,
        )

        purchase_request.title = "Reduced office supply request"
        purchase_request.description = "A reduced office supply purchase."
        purchase_request.business_justification = (
            "Required to maintain minimum operational stock."
        )
        purchase_request.category = RequestCategory.OFFICE_SUPPLIES
        purchase_request.requested_amount = Decimal("780.00")
        purchase_request.supplier = "OfficeHub Distribution"

        second_cycle = submit_purchase_request(
            purchase_request=purchase_request,
            requester=requester,
        )

        assert len(second_cycle.steps) == 1
        assert second_cycle.steps[0].step_type == StepType.MANAGER_APPROVAL
        assert second_cycle.steps[0].status == WorkflowStepStatus.ACTIVE


def test_resubmission_ui_creates_new_cycle(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """The submission route should support returned requests."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        purchase_request = create_resubmission_environment(
            requester=requester,
            department=department,
        )

        purchase_request.title = "Returned request ready again"
        purchase_request.description = "Updated description after manager feedback."
        purchase_request.business_justification = (
            "Updated justification after manager feedback."
        )
        purchase_request.category = RequestCategory.HARDWARE
        purchase_request.requested_amount = Decimal("950.00")
        purchase_request.supplier = "Updated Supplier"

        db.session.commit()
        request_id = purchase_request.id

    login(
        client,
        active_user,
    )

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was submitted successfully" in response.data
    assert b"Cycle:" in response.data
    assert b"2" in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        cycles = list(
            db.session.scalars(
                select(WorkflowCycle).where(
                    WorkflowCycle.purchase_request_id == request_id
                )
            ).all()
        )

        assert stored_request is not None
        assert stored_request.status == RequestStatus.IN_REVIEW
        assert stored_request.current_revision_number == 2
        assert len(cycles) == 2
