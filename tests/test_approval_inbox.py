"""Tests for the approval inbox and decision routes."""

from datetime import date
from decimal import Decimal

from app.authorization import RoleName
from app.extensions import db
from app.models import (
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
    WorkflowCycle,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.submission_service import submit_purchase_request
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


def assign_role(user: User, role_name: RoleName) -> None:
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
    """Create an active user."""
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


def login(client: FlaskClient, user: User) -> None:
    """Authenticate a user through the login route."""
    response = client.post(
        "/auth/login",
        data={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 302


def create_active_approval_task(
    *,
    requester: User,
    department: Department,
) -> tuple[PurchaseRequest, WorkflowStep, User]:
    """Create a submitted request with an active manager task."""
    assign_role(requester, RoleName.REQUESTER)

    manager = create_user(
        email="inbox.manager@aurevia.example",
        department=department,
        first_name="Morgan",
        last_name="Manager",
    )
    it_reviewer = create_user(
        email="inbox.it@aurevia.example",
        department=department,
        first_name="Isaac",
        last_name="Reviewer",
    )
    finance_approver = create_user(
        email="inbox.finance@aurevia.example",
        department=department,
        first_name="Fiona",
        last_name="Finance",
    )
    director = create_user(
        email="inbox.director@aurevia.example",
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
        name="Approval inbox workflow",
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
        title="Approval inbox test request",
        description="Request used to test approval routes.",
        business_justification="Required for route testing.",
        category=RequestCategory.SOFTWARE,
        supplier="Inbox Test Supplier",
        requested_amount=Decimal("7200.00"),
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

    manager_step = workflow_cycle.steps[0]

    return purchase_request, manager_step, manager


def test_assigned_manager_can_view_approval_inbox(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An assigned manager should see their active task."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, _, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        title = purchase_request.title
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.get("/approvals/")

    assert response.status_code == 200
    assert b"Approval inbox" in response.data
    assert title.encode() in response.data
    assert b"Manager Approval" in response.data


def test_user_without_approver_role_cannot_open_inbox(
    client: FlaskClient,
    active_user: User,
) -> None:
    """A regular user should receive 403."""
    login(client, active_user)

    response = client.get("/approvals/")

    assert response.status_code == 403


def test_assigned_manager_can_open_task_detail(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An assigned approver should view task details."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, manager_step, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        step_id = manager_step.id
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.get(f"/approvals/{step_id}")

    assert response.status_code == 200
    assert b"Record decision" in response.data
    assert b"Approval inbox test request" in response.data
    assert b"Approve" in response.data
    assert b"Reject" in response.data
    assert b"Return for changes" in response.data


def test_unassigned_approver_cannot_view_task(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An unrelated approver should receive 404."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        _, manager_step, _ = create_active_approval_task(
            requester=requester,
            department=department,
        )

        outsider = create_user(
            email="inbox.outsider@aurevia.example",
            department=department,
            first_name="Other",
            last_name="Manager",
        )
        assign_role(outsider, RoleName.MANAGER_APPROVER)

        step_id = manager_step.id
        outsider_id = outsider.id
        db.session.commit()

    with app.app_context():
        stored_outsider = db.session.get(User, outsider_id)

    login(client, stored_outsider)

    response = client.get(f"/approvals/{step_id}")

    assert response.status_code == 404


def test_manager_can_approve_task_from_ui(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Approving through the UI should activate the next step."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, manager_step, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        request_id = purchase_request.id
        step_id = manager_step.id
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.post(
        f"/approvals/{step_id}/decision",
        data={
            "decision": DecisionType.APPROVE.value,
            "comment": "",
            "submit": "Record decision",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was completed with decision Approve" in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )
        stored_step = db.session.get(
            WorkflowStep,
            step_id,
        )

        assert stored_request.status == RequestStatus.IN_REVIEW
        assert stored_step.status == WorkflowStepStatus.APPROVED

        cycle = db.session.scalar(
            select(WorkflowCycle).where(WorkflowCycle.purchase_request_id == request_id)
        )

        assert cycle.steps[1].status == WorkflowStepStatus.ACTIVE


def test_manager_can_reject_task_from_ui(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Rejecting through the UI should reject the request."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, manager_step, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        request_id = purchase_request.id
        step_id = manager_step.id
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.post(
        f"/approvals/{step_id}/decision",
        data={
            "decision": DecisionType.REJECT.value,
            "comment": "The request is not sufficiently justified.",
            "submit": "Record decision",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was completed with decision Reject" in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert stored_request.status == RequestStatus.REJECTED


def test_return_for_changes_requires_comment(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A negative UI decision without comment should be rejected."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, manager_step, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        request_id = purchase_request.id
        step_id = manager_step.id
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.post(
        f"/approvals/{step_id}/decision",
        data={
            "decision": DecisionType.RETURN_FOR_CHANGES.value,
            "comment": "",
            "submit": "Record decision",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"A comment is required" in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )
        stored_step = db.session.get(
            WorkflowStep,
            step_id,
        )

        assert stored_request.status == RequestStatus.IN_REVIEW
        assert stored_step.status == WorkflowStepStatus.ACTIVE


def test_manager_can_return_request_for_changes(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Returning through the UI should make the request editable."""
    with app.app_context():
        requester = db.session.get(User, active_user.id)

        purchase_request, manager_step, manager = create_active_approval_task(
            requester=requester,
            department=department,
        )

        request_id = purchase_request.id
        step_id = manager_step.id
        manager_id = manager.id

    with app.app_context():
        stored_manager = db.session.get(User, manager_id)

    login(client, stored_manager)

    response = client.post(
        f"/approvals/{step_id}/decision",
        data={
            "decision": DecisionType.RETURN_FOR_CHANGES.value,
            "comment": "Please include a detailed cost breakdown.",
            "submit": "Record decision",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Return For Changes" in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert stored_request.status == RequestStatus.CHANGES_REQUESTED
