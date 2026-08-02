"""Purchase request routes."""

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy import select

from app.authorization import RoleName, roles_required
from app.extensions import db
from app.models import PurchaseRequest, RequestStatus
from app.requests import requests_bp
from app.requests.forms import PurchaseRequestDraftForm
from app.requests.policies import (
    can_cancel_request,
    can_edit_request,
    can_view_request,
)
from app.requests.services import (
    cancel_draft,
    create_draft,
    update_draft,
)


def get_owned_request_or_404(
    request_id: int,
) -> PurchaseRequest:
    """Return an owned purchase request without revealing unrelated IDs."""
    purchase_request = db.session.get(
        PurchaseRequest,
        request_id,
    )

    if purchase_request is None:
        abort(404)

    if not can_view_request(current_user, purchase_request):
        abort(404)

    return purchase_request


def populate_form_from_request(
    form: PurchaseRequestDraftForm,
    purchase_request: PurchaseRequest,
) -> None:
    """Populate an unsubmitted form with stored request values."""
    form.title.data = purchase_request.title
    form.description.data = purchase_request.description
    form.business_justification.data = purchase_request.business_justification
    form.category.data = (
        purchase_request.category.value if purchase_request.category else ""
    )
    form.supplier.data = purchase_request.supplier
    form.requested_amount.data = purchase_request.requested_amount
    form.expected_purchase_date.data = purchase_request.expected_purchase_date


@requests_bp.get("/")
@roles_required(RoleName.REQUESTER)
def list_requests():
    """Display purchase requests owned by the current user."""
    query = (
        select(PurchaseRequest)
        .where(PurchaseRequest.requester_id == current_user.id)
        .order_by(PurchaseRequest.created_at.desc())
    )

    status_value = request.args.get("status", "").strip().upper()

    if status_value:
        try:
            selected_status = RequestStatus(status_value)
        except ValueError:
            abort(400)

        query = query.where(PurchaseRequest.status == selected_status)

    purchase_requests = db.session.scalars(query).all()

    return render_template(
        "requests/list.html",
        purchase_requests=purchase_requests,
        statuses=RequestStatus,
        selected_status=status_value,
    )


@requests_bp.route("/new", methods=["GET", "POST"])
@roles_required(RoleName.REQUESTER)
def create_request():
    """Create a new purchase request draft."""
    form = PurchaseRequestDraftForm()

    if form.validate_on_submit():
        purchase_request = create_draft(
            current_user,
            form,
        )

        flash(
            f"Draft {purchase_request.reference_number} was saved.",
            "success",
        )

        return redirect(
            url_for(
                "requests.view_request",
                request_id=purchase_request.id,
            )
        )

    return render_template(
        "requests/create.html",
        form=form,
    )


@requests_bp.get("/<int:request_id>")
@roles_required(RoleName.REQUESTER)
def view_request(request_id: int):
    """Display one purchase request owned by the current user."""
    purchase_request = get_owned_request_or_404(request_id)

    return render_template(
        "requests/detail.html",
        purchase_request=purchase_request,
    )


@requests_bp.route(
    "/<int:request_id>/edit",
    methods=["GET", "POST"],
)
@roles_required(RoleName.REQUESTER)
def edit_request(request_id: int):
    """Edit an owned purchase request draft."""
    purchase_request = get_owned_request_or_404(request_id)

    if not can_edit_request(current_user, purchase_request):
        abort(409)

    form = PurchaseRequestDraftForm()

    if not form.is_submitted():
        populate_form_from_request(
            form,
            purchase_request,
        )

    if form.validate_on_submit():
        update_draft(
            purchase_request,
            form,
        )

        flash(
            f"Draft {purchase_request.reference_number} was updated.",
            "success",
        )

        return redirect(
            url_for(
                "requests.view_request",
                request_id=purchase_request.id,
            )
        )

    return render_template(
        "requests/edit.html",
        form=form,
        purchase_request=purchase_request,
    )


@requests_bp.post("/<int:request_id>/cancel")
@roles_required(RoleName.REQUESTER)
def cancel_request(request_id: int):
    """Cancel an owned purchase request draft."""
    purchase_request = get_owned_request_or_404(request_id)

    if not can_cancel_request(current_user, purchase_request):
        abort(409)

    cancel_draft(purchase_request)

    flash(
        f"Draft {purchase_request.reference_number} was cancelled.",
        "success",
    )

    return redirect(url_for("requests.list_requests"))
