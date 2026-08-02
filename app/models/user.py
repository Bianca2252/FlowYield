"""User model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.role import UserRole


class User(db.Model):
    """Represent an application user and employee."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "manager_id IS NULL OR manager_id != id",
            name="ck_users_manager_not_self",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
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
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    department: Mapped[Department] = relationship(
        back_populates="users",
    )
    manager: Mapped[User | None] = relationship(
        remote_side="User.id",
        back_populates="direct_reports",
        foreign_keys=[manager_id],
    )
    direct_reports: Mapped[list[User]] = relationship(
        back_populates="manager",
        foreign_keys=[manager_id],
    )
    role_assignments: Mapped[list[UserRole]] = relationship(
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    role_assignments_created: Mapped[list[UserRole]] = relationship(
        foreign_keys="UserRole.assigned_by_user_id",
        back_populates="assigned_by",
    )

    @property
    def full_name(self) -> str:
        """Return the user's display name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def roles(self) -> set[str]:
        """Return the names of the user's assigned roles."""
        return {assignment.role.name for assignment in self.role_assignments}

    def set_password(self, password: str) -> None:
        """Hash and store a plain-text password."""
        if not password:
            raise ValueError("Password must not be empty.")

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        """Return whether the user holds the requested role."""
        return role_name in self.roles

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<User {self.email}>"
