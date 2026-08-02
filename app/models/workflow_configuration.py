"""Versioned workflow configuration models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import StepType

if TYPE_CHECKING:
    from app.models.user import User


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class WorkflowConfiguration(db.Model):
    """Represent one immutable version of purchase workflow rules."""

    __tablename__ = "workflow_configurations"
    __table_args__ = (
        CheckConstraint(
            "version_number > 0",
            name="ck_workflow_configurations_positive_version",
        ),
        CheckConstraint(
            "low_value_threshold > 0",
            name="ck_workflow_configurations_positive_low_threshold",
        ),
        CheckConstraint(
            "high_value_threshold > 0",
            name="ck_workflow_configurations_positive_high_threshold",
        ),
        CheckConstraint(
            "it_review_threshold > 0",
            name="ck_workflow_configurations_positive_it_threshold",
        ),
        CheckConstraint(
            "low_value_threshold < high_value_threshold",
            name="ck_workflow_configurations_threshold_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    version_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    low_value_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("1000.00"),
    )

    high_value_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("10000.00"),
    )

    it_review_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("5000.00"),
    )

    it_review_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_by: Mapped[User] = relationship(
        foreign_keys=[created_by_user_id],
    )

    step_configurations: Mapped[list[StepConfiguration]] = relationship(
        back_populates="workflow_configuration",
        cascade="all, delete-orphan",
        order_by="StepConfiguration.sequence_hint",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<WorkflowConfiguration "
            f"version={self.version_number} "
            f"active={self.is_active}>"
        )


class StepConfiguration(db.Model):
    """Store SLA and assignment settings for one workflow step type."""

    __tablename__ = "step_configurations"
    __table_args__ = (
        UniqueConstraint(
            "workflow_configuration_id",
            "step_type",
            name="uq_step_configurations_workflow_step_type",
        ),
        CheckConstraint(
            "sla_duration_hours > 0",
            name="ck_step_configurations_positive_sla",
        ),
        CheckConstraint(
            "sequence_hint > 0",
            name="ck_step_configurations_positive_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_configuration_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workflow_configurations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    step_type: Mapped[StepType] = mapped_column(
        Enum(
            StepType,
            name="workflow_step_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    sla_duration_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    default_assignee_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    required_role_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    sequence_hint: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    workflow_configuration: Mapped[WorkflowConfiguration] = relationship(
        back_populates="step_configurations",
    )

    default_assignee: Mapped[User | None] = relationship(
        foreign_keys=[default_assignee_user_id],
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<StepConfiguration "
            f"type={self.step_type.value} "
            f"sla={self.sla_duration_hours}>"
        )
