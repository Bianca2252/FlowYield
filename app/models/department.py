"""Department model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.purchase_request import PurchaseRequest, RequestRevision
    from app.models.user import User


class Department(db.Model):
    """Represent an organizational department."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    users: Mapped[list[User]] = relationship(
        back_populates="department",
    )

    purchase_requests: Mapped[list[PurchaseRequest]] = relationship(
        back_populates="department",
    )

    request_revisions: Mapped[list[RequestRevision]] = relationship(
        back_populates="department",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<Department {self.code}>"
