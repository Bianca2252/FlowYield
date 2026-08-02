"""Workflow execution database models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import (
    DecisionType,
    SLAResult,
    StepType,
    WorkflowCycleStatus,
    WorkflowStepStatus,
)

if TYPE_CHECKING:
    from app.models.purchase_request import (
        PurchaseRequest,
        RequestRevision,
    )
    from app.models.user import User
    from app.models.workflow_configuration import WorkflowConfiguration


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class WorkflowCycle(db.Model):
    """Represent one approval attempt for one request revision."""

    __tablename__ = "workflow_cycles"
    __table_args__ = (
        UniqueConstraint(
            "purchase_request_id",
            "cycle_number",
            name="uq_workflow_cycles_request_cycle",
        ),
        UniqueConstraint(
            "request_revision_id",
            name="uq_workflow_cycles_request_revision",
        ),
        CheckConstraint(
            "cycle_number > 0",
            name="ck_workflow_cycles_positive_cycle_number",
        ),
        Index(
            "ix_workflow_cycles_status_started_at",
            "status",
            "started_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requests.id"),
        nullable=False,
        index=True,
    )

    request_revision_id: Mapped[int] = mapped_column(
        ForeignKey("request_revisions.id"),
        nullable=False,
        index=True,
    )

    workflow_configuration_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_configurations.id"),
        nullable=False,
        index=True,
    )

    cycle_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[WorkflowCycleStatus] = mapped_column(
        Enum(
            WorkflowCycleStatus,
            name="workflow_cycle_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=WorkflowCycleStatus.ACTIVE,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    superseded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    purchase_request: Mapped[PurchaseRequest] = relationship(
        backref="workflow_cycles",
    )

    request_revision: Mapped[RequestRevision] = relationship(
        backref="workflow_cycle",
    )

    workflow_configuration: Mapped[WorkflowConfiguration] = relationship(
        backref="workflow_cycles",
    )

    steps: Mapped[list[WorkflowStep]] = relationship(
        back_populates="workflow_cycle",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.sequence_number",
    )

    decisions: Mapped[list[ApprovalDecision]] = relationship(
        back_populates="workflow_cycle",
        cascade="all, delete-orphan",
        order_by="ApprovalDecision.decided_at",
    )

    @property
    def active_step(self) -> WorkflowStep | None:
        """Return the currently active workflow step."""
        return next(
            (step for step in self.steps if step.status == WorkflowStepStatus.ACTIVE),
            None,
        )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<WorkflowCycle request={self.purchase_request_id} "
            f"cycle={self.cycle_number}>"
        )


class WorkflowStep(db.Model):
    """Represent one sequential approval step in a workflow cycle."""

    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint(
            "workflow_cycle_id",
            "sequence_number",
            name="uq_workflow_steps_cycle_sequence",
        ),
        CheckConstraint(
            "sequence_number > 0",
            name="ck_workflow_steps_positive_sequence",
        ),
        CheckConstraint(
            "sla_duration_hours > 0",
            name="ck_workflow_steps_positive_sla",
        ),
        CheckConstraint(
            "overdue_seconds IS NULL OR overdue_seconds >= 0",
            name="ck_workflow_steps_non_negative_overdue",
        ),
        Index(
            "ix_workflow_steps_assignee_status",
            "assigned_user_id",
            "status",
        ),
        Index(
            "ix_workflow_steps_status_deadline",
            "status",
            "deadline_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_cycle_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    step_type: Mapped[StepType] = mapped_column(
        Enum(
            StepType,
            name="execution_step_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    required_role_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    assigned_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[WorkflowStepStatus] = mapped_column(
        Enum(
            WorkflowStepStatus,
            name="workflow_step_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=WorkflowStepStatus.PENDING,
        index=True,
    )

    reason_for_inclusion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    sla_duration_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sla_result: Mapped[SLAResult | None] = mapped_column(
        Enum(
            SLAResult,
            name="workflow_step_sla_result",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
    )

    overdue_seconds: Mapped[int | None] = mapped_column(
        Integer,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    workflow_cycle: Mapped[WorkflowCycle] = relationship(
        back_populates="steps",
    )

    assigned_user: Mapped[User] = relationship(
        backref="assigned_workflow_steps",
    )

    decision: Mapped[ApprovalDecision | None] = relationship(
        back_populates="workflow_step",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def is_actionable(self) -> bool:
        """Return whether the step may currently receive a decision."""
        return self.status == WorkflowStepStatus.ACTIVE and self.decision is None

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<WorkflowStep cycle={self.workflow_cycle_id} "
            f"sequence={self.sequence_number} "
            f"type={self.step_type.value}>"
        )


class ApprovalDecision(db.Model):
    """Store the authoritative human decision for a workflow step."""

    __tablename__ = "approval_decisions"
    __table_args__ = (
        UniqueConstraint(
            "workflow_step_id",
            name="uq_approval_decisions_workflow_step",
        ),
        CheckConstraint(
            """
            decision = 'APPROVE'
            OR (
                comment IS NOT NULL
                AND length(trim(comment)) > 0
            )
            """,
            name="ck_approval_decisions_comment_required",
        ),
        Index(
            "ix_approval_decisions_request_decided_at",
            "purchase_request_id",
            "decided_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_step_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_steps.id"),
        nullable=False,
        index=True,
    )

    workflow_cycle_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_cycles.id"),
        nullable=False,
        index=True,
    )

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requests.id"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    decision: Mapped[DecisionType] = mapped_column(
        Enum(
            DecisionType,
            name="approval_decision_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    workflow_step: Mapped[WorkflowStep] = relationship(
        back_populates="decision",
    )

    workflow_cycle: Mapped[WorkflowCycle] = relationship(
        back_populates="decisions",
    )

    purchase_request: Mapped[PurchaseRequest] = relationship(
        backref="approval_decisions",
    )

    actor: Mapped[User] = relationship(
        backref="approval_decisions",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<ApprovalDecision step={self.workflow_step_id} "
            f"decision={self.decision.value}>"
        )
