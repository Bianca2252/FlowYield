"""Approval inbox and decision routes."""

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from sqlalchemy import select

from app.approvals import approvals_bp
from app.approvals.forms import ApprovalDecisionForm
from app.authorization import RoleName, roles_required
from app.extensions import db
from app.models import (
    DecisionType,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.workflows.decision_service import (
    record_approval_decision,
)
from app.workflows.exceptions import WorkflowError

APPROVER_ROLES = (
    RoleName.MANAGER_APPROVER,
    RoleName.IT_REVIEWER,
    RoleName.FINANCE_APPROVER,
    RoleName.DIRECTOR_APPROVER,
)


def get_assigned_step_or_404(
    step_id: int,
) -> WorkflowStep:
    """Return a workflow step assigned to the current user."""
    workflow_step = db.session.get(
        WorkflowStep,
        step_id,
    )

    if workflow_step is None:
        abort(404)

    if workflow_step.assigned_user_id != current_user.id:
        abort(404)

    return workflow_step


@approvals_bp.get("/")
@roles_required(*APPROVER_ROLES)
def inbox():
    """Display active approval tasks assigned to the current user."""
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
    )

    workflow_steps = list(db.session.scalars(query).all())

    return render_template(
        "approvals/list.html",
        workflow_steps=workflow_steps,
    )


@approvals_bp.get("/<int:step_id>")
@roles_required(*APPROVER_ROLES)
def view_task(step_id: int):
    """Display one workflow task assigned to the current user."""
    workflow_step = get_assigned_step_or_404(step_id)
    form = ApprovalDecisionForm()

    return render_template(
        "approvals/detail.html",
        workflow_step=workflow_step,
        purchase_request=(workflow_step.workflow_cycle.purchase_request),
        form=form,
    )


@approvals_bp.post("/<int:step_id>/decision")
@roles_required(*APPROVER_ROLES)
def decide_task(step_id: int):
    """Record a decision for an assigned active workflow step."""
    workflow_step = get_assigned_step_or_404(step_id)
    form = ApprovalDecisionForm()

    if not form.validate_on_submit():
        flash(
            "The approval decision form is invalid.",
            "danger",
        )

        return render_template(
            "approvals/detail.html",
            workflow_step=workflow_step,
            purchase_request=(workflow_step.workflow_cycle.purchase_request),
            form=form,
        ), 400

    try:
        decision = DecisionType(form.decision.data)

        record_approval_decision(
            workflow_step=workflow_step,
            actor=current_user,
            decision=decision,
            comment=form.comment.data,
        )
    except WorkflowError as error:
        flash(
            str(error),
            "danger",
        )

        return redirect(
            url_for(
                "approvals.view_task",
                step_id=workflow_step.id,
            )
        )
    except ValueError:
        flash(
            "The selected approval decision is invalid.",
            "danger",
        )

        return redirect(
            url_for(
                "approvals.view_task",
                step_id=workflow_step.id,
            )
        )

    flash(
        (
            f"{workflow_step.step_type.value.replace('_', ' ').title()} "
            f"was completed with decision "
            f"{decision.value.replace('_', ' ').title()}."
        ),
        "success",
    )

    return redirect(url_for("approvals.inbox"))
