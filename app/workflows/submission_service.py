"""Purchase request submission and workflow initialization service."""

from datetime import UTC, datetime, timedelta

from app.extensions import db
from app.models import (
    PurchaseRequest,
    RequestRevision,
    RequestStatus,
    User,
    WorkflowCycle,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.assignments import assign_approval_path
from app.workflows.configuration_service import (
    get_active_workflow_configuration,
)
from app.workflows.exceptions import (
    InvalidTransitionError,
    RequestValidationError,
)
from app.workflows.rules import build_approval_path


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def validate_request_for_submission(
    purchase_request: PurchaseRequest,
    requester: User,
) -> None:
    """Validate ownership, state, and required request fields."""
    if purchase_request.requester_id != requester.id:
        raise RequestValidationError("Only the request owner may submit this request.")

    if purchase_request.status not in {
        RequestStatus.DRAFT,
        RequestStatus.CHANGES_REQUESTED,
    }:
        raise InvalidTransitionError(
            "Only draft or returned requests may be submitted."
        )

    required_text_fields = {
        "title": purchase_request.title,
        "description": purchase_request.description,
        "business justification": (purchase_request.business_justification),
    }

    for field_name, value in required_text_fields.items():
        if value is None or not value.strip():
            raise RequestValidationError(f"The {field_name} field is required.")

    if purchase_request.category is None:
        raise RequestValidationError("The request category is required.")

    if purchase_request.requested_amount is None:
        raise RequestValidationError("The requested amount is required.")

    if purchase_request.requested_amount <= 0:
        raise RequestValidationError("The requested amount must be greater than zero.")

    if purchase_request.currency != "EUR":
        raise RequestValidationError("Only EUR purchase requests are supported.")

    if purchase_request.expected_purchase_date is None:
        raise RequestValidationError("The expected purchase date is required.")

    if purchase_request.department_id is None:
        raise RequestValidationError("The request department is required.")


def create_request_revision(
    *,
    purchase_request: PurchaseRequest,
    requester: User,
    revision_number: int,
    submitted_at: datetime,
) -> RequestRevision:
    """Create an immutable snapshot of submitted request values."""
    revision = RequestRevision(
        purchase_request_id=purchase_request.id,
        revision_number=revision_number,
        title=purchase_request.title,
        description=purchase_request.description,
        business_justification=(purchase_request.business_justification),
        category=purchase_request.category,
        supplier=purchase_request.supplier,
        requested_amount=purchase_request.requested_amount,
        currency=purchase_request.currency,
        expected_purchase_date=(purchase_request.expected_purchase_date),
        department_id=purchase_request.department_id,
        submitted_by_user_id=requester.id,
        submitted_at=submitted_at,
    )

    db.session.add(revision)
    db.session.flush()

    return revision


def create_workflow_cycle(
    *,
    purchase_request: PurchaseRequest,
    request_revision: RequestRevision,
    workflow_configuration_id: int,
    cycle_number: int,
    started_at: datetime,
) -> WorkflowCycle:
    """Create the workflow cycle for one submitted revision."""
    workflow_cycle = WorkflowCycle(
        purchase_request_id=purchase_request.id,
        request_revision_id=request_revision.id,
        workflow_configuration_id=workflow_configuration_id,
        cycle_number=cycle_number,
        started_at=started_at,
    )

    db.session.add(workflow_cycle)
    db.session.flush()

    return workflow_cycle


def create_workflow_steps(
    *,
    workflow_cycle: WorkflowCycle,
    assigned_steps,
    activated_at: datetime,
) -> list[WorkflowStep]:
    """Create sequential workflow steps and activate the first one."""
    workflow_steps: list[WorkflowStep] = []

    for assigned_step in assigned_steps:
        is_first_step = assigned_step.sequence_number == 1

        workflow_step = WorkflowStep(
            workflow_cycle_id=workflow_cycle.id,
            step_type=assigned_step.step_type,
            sequence_number=assigned_step.sequence_number,
            required_role_name=assigned_step.required_role_name,
            assigned_user_id=assigned_step.assigned_user.id,
            status=(
                WorkflowStepStatus.ACTIVE
                if is_first_step
                else WorkflowStepStatus.PENDING
            ),
            reason_for_inclusion=(assigned_step.reason_for_inclusion),
            activated_at=activated_at if is_first_step else None,
            deadline_at=(
                activated_at + timedelta(hours=assigned_step.sla_duration_hours)
                if is_first_step
                else None
            ),
            sla_duration_hours=(assigned_step.sla_duration_hours),
        )

        db.session.add(workflow_step)
        workflow_steps.append(workflow_step)

    db.session.flush()

    return workflow_steps


def submit_purchase_request(
    *,
    purchase_request: PurchaseRequest,
    requester: User,
) -> WorkflowCycle:
    """Submit a request and initialize its workflow atomically."""
    validate_request_for_submission(
        purchase_request,
        requester,
    )

    workflow_configuration = get_active_workflow_configuration()

    approval_path = build_approval_path(
        amount=purchase_request.requested_amount,
        category=purchase_request.category,
        configuration=workflow_configuration,
    )

    assigned_steps = assign_approval_path(
        requester=requester,
        approval_path=approval_path,
        workflow_configuration=workflow_configuration,
    )

    submitted_at = utc_now()
    revision_number = purchase_request.current_revision_number + 1
    cycle_number = revision_number

    try:
        request_revision = create_request_revision(
            purchase_request=purchase_request,
            requester=requester,
            revision_number=revision_number,
            submitted_at=submitted_at,
        )

        workflow_cycle = create_workflow_cycle(
            purchase_request=purchase_request,
            request_revision=request_revision,
            workflow_configuration_id=workflow_configuration.id,
            cycle_number=cycle_number,
            started_at=submitted_at,
        )

        create_workflow_steps(
            workflow_cycle=workflow_cycle,
            assigned_steps=assigned_steps,
            activated_at=submitted_at,
        )

        purchase_request.current_revision_number = revision_number
        purchase_request.status = RequestStatus.IN_REVIEW
        purchase_request.submitted_at = submitted_at
        purchase_request.completed_at = None
        purchase_request.cancelled_at = None

        db.session.commit()

        return workflow_cycle

    except Exception:
        db.session.rollback()
        raise
