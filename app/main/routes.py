"""Routes for the main application area."""

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.extensions import db
from app.main import main_bp
from app.models import (
    PurchaseRequest,
    RequestStatus,
    WorkflowStep,
    WorkflowStepStatus,
)


def get_requester_metrics() -> dict[str, int]:
    """Return purchase request totals for the current requester."""
    base_filters = (PurchaseRequest.requester_id == current_user.id,)

    total_requests = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
        )
    )

    draft_requests = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
            PurchaseRequest.status == RequestStatus.DRAFT,
        )
    )

    in_review_requests = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
            PurchaseRequest.status == RequestStatus.IN_REVIEW,
        )
    )

    approved_requests = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
            PurchaseRequest.status == RequestStatus.APPROVED,
        )
    )

    rejected_requests = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
            PurchaseRequest.status == RequestStatus.REJECTED,
        )
    )

    changes_requested = db.session.scalar(
        select(func.count(PurchaseRequest.id)).where(
            *base_filters,
            PurchaseRequest.status == RequestStatus.CHANGES_REQUESTED,
        )
    )

    return {
        "total": total_requests or 0,
        "draft": draft_requests or 0,
        "in_review": in_review_requests or 0,
        "approved": approved_requests or 0,
        "rejected": rejected_requests or 0,
        "changes_requested": changes_requested or 0,
    }


def get_approval_metrics() -> dict[str, int]:
    """Return active and overdue approval task counts."""
    active_tasks = db.session.scalar(
        select(func.count(WorkflowStep.id)).where(
            WorkflowStep.assigned_user_id == current_user.id,
            WorkflowStep.status == WorkflowStepStatus.ACTIVE,
        )
    )

    overdue_tasks = db.session.scalar(
        select(func.count(WorkflowStep.id)).where(
            WorkflowStep.assigned_user_id == current_user.id,
            WorkflowStep.status == WorkflowStepStatus.ACTIVE,
            WorkflowStep.deadline_at < func.now(),
        )
    )

    completed_tasks = db.session.scalar(
        select(func.count(WorkflowStep.id)).where(
            WorkflowStep.assigned_user_id == current_user.id,
            WorkflowStep.status.in_(
                {
                    WorkflowStepStatus.APPROVED,
                    WorkflowStepStatus.REJECTED,
                    WorkflowStepStatus.CHANGES_REQUESTED,
                }
            ),
        )
    )

    return {
        "active": active_tasks or 0,
        "overdue": overdue_tasks or 0,
        "completed": completed_tasks or 0,
    }


def get_recent_requests() -> list[PurchaseRequest]:
    """Return recent purchase requests owned by the current user."""
    if not current_user.has_role("REQUESTER"):
        return []

    query = (
        select(PurchaseRequest)
        .where(
            PurchaseRequest.requester_id == current_user.id,
        )
        .order_by(
            PurchaseRequest.updated_at.desc(),
        )
        .limit(5)
    )

    return list(db.session.scalars(query).all())


def get_active_approval_tasks() -> list[WorkflowStep]:
    """Return the current user's most urgent approval tasks."""
    approver_roles = {
        "MANAGER_APPROVER",
        "IT_REVIEWER",
        "FINANCE_APPROVER",
        "DIRECTOR_APPROVER",
    }

    if not current_user.roles.intersection(approver_roles):
        return []

    query = (
        select(WorkflowStep)
        .where(
            WorkflowStep.assigned_user_id == current_user.id,
            WorkflowStep.status == WorkflowStepStatus.ACTIVE,
        )
        .order_by(
            WorkflowStep.deadline_at.asc(),
            WorkflowStep.created_at.asc(),
        )
        .limit(5)
    )

    return list(db.session.scalars(query).all())


@main_bp.get("/")
def index():
    """Redirect visitors to the main dashboard experience."""
    if current_user.is_authenticated:
        return render_template(
            "main/index.html",
            authenticated=True,
        )

    return render_template(
        "main/index.html",
        authenticated=False,
    )


@main_bp.get("/dashboard")
@login_required
def dashboard():
    """Display a role-aware application dashboard."""
    requester_metrics = (
        get_requester_metrics() if current_user.has_role("REQUESTER") else None
    )

    approver_roles = {
        "MANAGER_APPROVER",
        "IT_REVIEWER",
        "FINANCE_APPROVER",
        "DIRECTOR_APPROVER",
    }

    approval_metrics = (
        get_approval_metrics()
        if current_user.roles.intersection(approver_roles)
        else None
    )

    return render_template(
        "main/dashboard.html",
        requester_metrics=requester_metrics,
        approval_metrics=approval_metrics,
        recent_requests=get_recent_requests(),
        active_approval_tasks=get_active_approval_tasks(),
    )
