"""Tests for the purchase request submission user interface."""

from datetime import date
from decimal import Decimal

from app.authorization import RoleName
from app.extensions import db
from app.models import (
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


def create_submission_environment(
    *,
    requester: User,
    department: Department,
) -> None:
    """Create roles, approvers, and an active workflow configuration."""
    assign_role(
        requester,
        RoleName.REQUESTER,
    )

    manager = create_user(
        email="ui.manager@aurevia.example",
        department_id=department.id,
        first_name="Morgan",
        last_name="Manager",
    )
    it_reviewer = create_user(
        email="ui.it@aurevia.example",
        department_id=department.id,
        first_name="Isaac",
        last_name="Reviewer",
    )
    finance_approver = create_user(
        email="ui.finance@aurevia.example",
        department_id=department.id,
        first_name="Fiona",
        last_name="Finance",
    )
    director_approver = create_user(
        email="ui.director@aurevia.example",
        department_id=department.id,
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
        director_approver,
        RoleName.DIRECTOR_APPROVER,
    )

    requester.manager = manager

    configuration = WorkflowConfiguration(
        version_number=1,
        name="Submission UI workflow",
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
                default_assignee=director_approver,
            ),
        ]
    )

    db.session.add(configuration)
    db.session.commit()


def create_complete_request(
    *,
    requester: User,
    department: Department,
    title: str = "Annual software licenses",
    amount: Decimal = Decimal("7200.00"),
    category: RequestCategory = RequestCategory.SOFTWARE,
) -> PurchaseRequest:
    """Create a complete draft ready for submission."""
    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=department.id,
        title=title,
        description="Annual licenses for the Sales department.",
        business_justification=("The licenses are required for ongoing client work."),
        category=category,
        supplier="Aurevia Software Partner",
        requested_amount=amount,
        currency="EUR",
        expected_purchase_date=date(2026, 10, 1),
        status=RequestStatus.DRAFT,
    )

    db.session.add(purchase_request)
    db.session.commit()

    return purchase_request


def test_request_detail_displays_submit_button_for_draft(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """A draft detail page should display submission controls."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(client, active_user)

    response = client.get(f"/requests/{request_id}")

    assert response.status_code == 200
    assert b"Submit request" in response.data
    assert b"Edit request" in response.data
    assert b"Draft" in response.data


def test_requester_can_submit_complete_request_from_ui(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Posting the submission form should initialize the workflow."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/requests/{request_id}")

    with app.app_context():
        submitted_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert submitted_request is not None
        assert submitted_request.status == RequestStatus.IN_REVIEW
        assert submitted_request.current_revision_number == 1
        assert submitted_request.submitted_at is not None

        workflow_cycle = db.session.scalar(
            select(WorkflowCycle).where(WorkflowCycle.purchase_request_id == request_id)
        )

        assert workflow_cycle is not None
        assert workflow_cycle.cycle_number == 1

        workflow_steps = list(
            db.session.scalars(
                select(WorkflowStep)
                .where(WorkflowStep.workflow_cycle_id == workflow_cycle.id)
                .order_by(WorkflowStep.sequence_number)
            ).all()
        )

        assert len(workflow_steps) == 3
        assert workflow_steps[0].status == WorkflowStepStatus.ACTIVE
        assert workflow_steps[1].status == WorkflowStepStatus.PENDING
        assert workflow_steps[2].status == WorkflowStepStatus.PENDING


def test_successful_submission_displays_workflow_on_detail_page(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """The redirected page should display generated workflow steps."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was submitted successfully" in response.data
    assert b"Approval workflow" in response.data
    assert b"Manager Approval" in response.data
    assert b"It Review" in response.data
    assert b"Finance Approval" in response.data
    assert b"Active" in response.data
    assert b"Pending" in response.data
    assert b"Morgan" in response.data
    assert b"Manager" in response.data
    assert b"Isaac" in response.data
    assert b"Reviewer" in response.data
    assert b"Fiona" in response.data
    assert b"Finance" in response.data


def test_incomplete_request_submission_shows_validation_error(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An incomplete request should remain a draft."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        purchase_request.business_justification = None
        db.session.commit()

        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"The business justification field is required." in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert stored_request is not None
        assert stored_request.status == RequestStatus.DRAFT
        assert stored_request.current_revision_number == 0


def test_submission_error_is_displayed_when_manager_is_missing(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Assignment failures should appear as controlled UI errors."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )
        requester.manager = None

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
        )

        db.session.commit()
        request_id = purchase_request.id

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"The requester does not have a configured manager." in response.data

    with app.app_context():
        stored_request = db.session.get(
            PurchaseRequest,
            request_id,
        )

        assert stored_request is not None
        assert stored_request.status == RequestStatus.DRAFT


def test_submitted_request_no_longer_displays_submit_button(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """An in-review request should not display draft actions."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(client, active_user)

    client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
    )

    response = client.get(f"/requests/{request_id}")

    assert response.status_code == 200
    assert b"In Review" in response.data
    assert b"Approval workflow" in response.data
    assert b"Submit request" not in response.data
    assert b"Cancel draft" not in response.data


def test_requester_cannot_submit_another_users_request(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Submission should hide requests owned by another user."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        other_user = create_user(
            email="ui.other@aurevia.example",
            department_id=department.id,
            first_name="Other",
            last_name="Requester",
        )
        assign_role(
            other_user,
            RoleName.REQUESTER,
        )

        purchase_request = create_complete_request(
            requester=other_user,
            department=department,
        )
        request_id = purchase_request.id

        db.session.commit()

    login(client, active_user)

    response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
    )

    assert response.status_code == 404


def test_repeated_ui_submission_is_rejected_without_duplicates(
    app: Flask,
    client: FlaskClient,
    active_user: User,
    department: Department,
) -> None:
    """Submitting twice should not create duplicate workflow cycles."""
    with app.app_context():
        requester = db.session.get(
            User,
            active_user.id,
        )

        create_submission_environment(
            requester=requester,
            department=department,
        )

        purchase_request = create_complete_request(
            requester=requester,
            department=department,
        )
        request_id = purchase_request.id

    login(client, active_user)

    first_response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
    )

    second_response = client.post(
        f"/requests/{request_id}/submit",
        data={
            "submit": "Submit request",
        },
        follow_redirects=True,
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 200
    assert b"Only draft or returned requests may be submitted." in second_response.data

    with app.app_context():
        workflow_cycles = list(
            db.session.scalars(
                select(WorkflowCycle).where(
                    WorkflowCycle.purchase_request_id == request_id
                )
            ).all()
        )

        assert len(workflow_cycles) == 1
