"""Object-level purchase request authorization policies."""

from app.models import PurchaseRequest, RequestStatus, User


def can_view_request(
    user: User,
    purchase_request: PurchaseRequest,
) -> bool:
    """Return whether a user may view a purchase request."""
    return purchase_request.requester_id == user.id


def can_edit_request(
    user: User,
    purchase_request: PurchaseRequest,
) -> bool:
    """Return whether a user may edit a purchase request."""
    return purchase_request.requester_id == user.id and purchase_request.status in {
        RequestStatus.DRAFT,
        RequestStatus.CHANGES_REQUESTED,
    }


def can_cancel_request(
    user: User,
    purchase_request: PurchaseRequest,
) -> bool:
    """Return whether a user may cancel a purchase request."""
    return (
        purchase_request.requester_id == user.id
        and purchase_request.status == RequestStatus.DRAFT
    )
