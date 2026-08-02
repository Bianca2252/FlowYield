"""Purchase request domain models."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import CommentType, RequestCategory, RequestStatus

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def generate_purchase_request_reference() -> str:
    """Generate a human-readable purchase request reference."""
    date_component = datetime.now(UTC).strftime("%Y%m%d")
    unique_component = uuid4().hex[:8].upper()

    return f"PR-{date_component}-{unique_component}"


class PurchaseRequest(db.Model):
    """Represent the current state of a purchase request."""

    __tablename__ = "purchase_requests"
    __table_args__ = (
        CheckConstraint(
            "requested_amount IS NULL OR requested_amount > 0",
            name="ck_purchase_requests_positive_amount",
        ),
        CheckConstraint(
            "currency = 'EUR'",
            name="ck_purchase_requests_eur_currency",
        ),
        CheckConstraint(
            "current_revision_number >= 0",
            name="ck_purchase_requests_revision_non_negative",
        ),
        Index(
            "ix_purchase_requests_status_created_at",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    reference_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        default=generate_purchase_request_reference,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    business_justification: Mapped[str | None] = mapped_column(
        Text,
    )

    category: Mapped[RequestCategory | None] = mapped_column(
        Enum(
            RequestCategory,
            name="request_category",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
    )

    supplier: Mapped[str | None] = mapped_column(
        String(200),
    )

    requested_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
    )

    expected_purchase_date: Mapped[date | None] = mapped_column(
        Date,
    )

    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=RequestStatus.DRAFT,
        index=True,
    )

    current_revision_number: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
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

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    requester: Mapped[User] = relationship(
        foreign_keys=[requester_id],
        back_populates="purchase_requests",
    )

    department: Mapped[Department] = relationship(
        back_populates="purchase_requests",
    )

    revisions: Mapped[list[RequestRevision]] = relationship(
        back_populates="purchase_request",
        cascade="all, delete-orphan",
        order_by="RequestRevision.revision_number",
    )

    comments: Mapped[list[RequestComment]] = relationship(
        back_populates="purchase_request",
        cascade="all, delete-orphan",
        order_by="RequestComment.created_at",
    )

    @property
    def is_editable(self) -> bool:
        """Return whether the request may currently be edited."""
        return self.status in {
            RequestStatus.DRAFT,
            RequestStatus.CHANGES_REQUESTED,
        }

    @property
    def is_final(self) -> bool:
        """Return whether the request has reached a final state."""
        return self.status in {
            RequestStatus.APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.CANCELLED,
        }

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<PurchaseRequest {self.reference_number}>"


class RequestRevision(db.Model):
    """Store an immutable submitted snapshot of a purchase request."""

    __tablename__ = "request_revisions"
    __table_args__ = (
        UniqueConstraint(
            "purchase_request_id",
            "revision_number",
            name="uq_request_revisions_request_revision",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_request_revisions_positive_revision",
        ),
        CheckConstraint(
            "requested_amount > 0",
            name="ck_request_revisions_positive_amount",
        ),
        CheckConstraint(
            "currency = 'EUR'",
            name="ck_request_revisions_eur_currency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    revision_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    business_justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[RequestCategory] = mapped_column(
        Enum(
            RequestCategory,
            name="revision_request_category",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    supplier: Mapped[str | None] = mapped_column(
        String(200),
    )

    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
    )

    expected_purchase_date: Mapped[date | None] = mapped_column(
        Date,
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )

    submitted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    change_summary: Mapped[str | None] = mapped_column(
        Text,
    )

    purchase_request: Mapped[PurchaseRequest] = relationship(
        back_populates="revisions",
    )

    department: Mapped[Department] = relationship(
        back_populates="request_revisions",
    )

    submitted_by: Mapped[User] = relationship(
        foreign_keys=[submitted_by_user_id],
        back_populates="submitted_request_revisions",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<RequestRevision request={self.purchase_request_id} "
            f"revision={self.revision_number}>"
        )


class RequestComment(db.Model):
    """Represent a comment associated with a purchase request."""

    __tablename__ = "request_comments"
    __table_args__ = (
        CheckConstraint(
            "length(trim(body)) > 0",
            name="ck_request_comments_body_not_empty",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    comment_type: Mapped[CommentType] = mapped_column(
        Enum(
            CommentType,
            name="request_comment_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=CommentType.GENERAL,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    purchase_request: Mapped[PurchaseRequest] = relationship(
        back_populates="comments",
    )

    author: Mapped[User | None] = relationship(
        foreign_keys=[author_id],
        back_populates="request_comments",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<RequestComment request={self.purchase_request_id}>"
