"""Role and user-role association models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.user import User


class Role(db.Model):
    """Represent a named application role."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    user_assignments: Mapped[list[UserRole]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<Role {self.name}>"


class UserRole(db.Model):
    """Represent one role assignment to one user."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_roles_user_id_role_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
        back_populates="role_assignments",
    )
    role: Mapped[Role] = relationship(
        back_populates="user_assignments",
    )
    assigned_by: Mapped[User | None] = relationship(
        foreign_keys=[assigned_by_user_id],
        back_populates="role_assignments_created",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<UserRole user={self.user_id} role={self.role_id}>"
