"""Purchase request application services."""

from datetime import UTC, datetime
from decimal import Decimal

from app.extensions import db
from app.models import (
    PurchaseRequest,
    RequestCategory,
    RequestStatus,
    User,
)
from app.requests.forms import PurchaseRequestDraftForm


def optional_text(value: str | None) -> str | None:
    """Normalize optional text input."""
    if value is None:
        return None

    normalized_value = value.strip()

    return normalized_value or None


def apply_draft_form(
    purchase_request: PurchaseRequest,
    form: PurchaseRequestDraftForm,
) -> None:
    """Apply validated draft form values to a purchase request."""
    purchase_request.title = optional_text(form.title.data)
    purchase_request.description = optional_text(form.description.data)
    purchase_request.business_justification = optional_text(
        form.business_justification.data
    )
    purchase_request.category = (
        RequestCategory(form.category.data) if form.category.data else None
    )
    purchase_request.supplier = optional_text(form.supplier.data)
    purchase_request.requested_amount = (
        Decimal(form.requested_amount.data)
        if form.requested_amount.data is not None
        else None
    )
    purchase_request.expected_purchase_date = form.expected_purchase_date.data


def create_draft(
    requester: User,
    form: PurchaseRequestDraftForm,
) -> PurchaseRequest:
    """Create and persist a purchase request draft."""
    purchase_request = PurchaseRequest(
        requester_id=requester.id,
        department_id=requester.department_id,
        status=RequestStatus.DRAFT,
    )

    apply_draft_form(purchase_request, form)

    db.session.add(purchase_request)
    db.session.commit()

    return purchase_request


def update_draft(
    purchase_request: PurchaseRequest,
    form: PurchaseRequestDraftForm,
) -> PurchaseRequest:
    """Update and persist an existing purchase request draft."""
    if purchase_request.status != RequestStatus.DRAFT:
        raise ValueError("Only draft requests may be edited.")

    apply_draft_form(purchase_request, form)
    db.session.commit()

    return purchase_request


def cancel_draft(
    purchase_request: PurchaseRequest,
) -> PurchaseRequest:
    """Cancel an existing purchase request draft."""
    if purchase_request.status != RequestStatus.DRAFT:
        raise ValueError("Only draft requests may be cancelled.")

    purchase_request.status = RequestStatus.CANCELLED
    purchase_request.cancelled_at = datetime.now(UTC)

    db.session.commit()

    return purchase_request
