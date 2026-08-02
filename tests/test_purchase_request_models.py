"""Tests for purchase request domain models."""

from datetime import date
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import (
    CommentType,
    Department,
    PurchaseRequest,
    RequestCategory,
    RequestComment,
    RequestRevision,
    RequestStatus,
    User,
)
from flask import Flask
from sqlalchemy.exc import IntegrityError


def create_purchase_request(
    requester: User,
    department: Department,
    **overrides,
) -> PurchaseRequest:
    """Create a default purchase request for model tests."""
    values = {
        "requester_id": requester.id,
        "department_id": department.id,
        "title": "Development laptops",
        "description": "Purchase laptops for the engineering team.",
        "business_justification": (
            "Existing devices no longer meet development requirements."
        ),
        "category": RequestCategory.HARDWARE,
        "supplier": "Aurevia Hardware Partner",
        "requested_amount": Decimal("4500.00"),
        "currency": "EUR",
        "expected_purchase_date": date(2026, 10, 1),
    }
    values.update(overrides)

    request = PurchaseRequest(**values)
    db.session.add(request)
    db.session.flush()

    return request


def test_purchase_request_defaults(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A new request should begin as an editable draft."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
        )
        db.session.commit()

        assert request.id is not None
        assert request.reference_number.startswith("PR-")
        assert request.status == RequestStatus.DRAFT
        assert request.current_revision_number == 0
        assert request.currency == "EUR"
        assert request.is_editable is True
        assert request.is_final is False


def test_purchase_request_reference_is_unique(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Duplicate request references should be rejected."""
    with app.app_context():
        first_request = create_purchase_request(
            active_user,
            department,
            reference_number="PR-TEST-0001",
        )
        db.session.commit()

        duplicate_request = PurchaseRequest(
            reference_number=first_request.reference_number,
            requester_id=active_user.id,
            department_id=department.id,
        )
        db.session.add(duplicate_request)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_purchase_request_amount_must_be_positive(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A supplied request amount must be greater than zero."""
    with app.app_context():
        request = PurchaseRequest(
            requester_id=active_user.id,
            department_id=department.id,
            requested_amount=Decimal("0.00"),
        )
        db.session.add(request)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_request_final_state_properties(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Final request statuses should not be editable."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
            status=RequestStatus.APPROVED,
        )

        assert request.is_editable is False
        assert request.is_final is True


def test_request_revision_preserves_snapshot(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A revision should store submitted request values."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
        )

        revision = RequestRevision(
            purchase_request=request,
            revision_number=1,
            title=request.title,
            description=request.description,
            business_justification=request.business_justification,
            category=request.category,
            supplier=request.supplier,
            requested_amount=request.requested_amount,
            currency=request.currency,
            expected_purchase_date=request.expected_purchase_date,
            department_id=department.id,
            submitted_by_user_id=active_user.id,
        )

        db.session.add(revision)
        db.session.commit()

        assert revision.id is not None
        assert revision.revision_number == 1
        assert revision.requested_amount == Decimal("4500.00")
        assert revision.submitted_by == active_user
        assert revision in request.revisions


def test_revision_number_must_be_unique_per_request(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A request cannot contain duplicate revision numbers."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
        )

        revision_values = {
            "purchase_request": request,
            "revision_number": 1,
            "title": "Development laptops",
            "description": "Laptop purchase.",
            "business_justification": "Required for development.",
            "category": RequestCategory.HARDWARE,
            "requested_amount": Decimal("4500.00"),
            "currency": "EUR",
            "department_id": department.id,
            "submitted_by_user_id": active_user.id,
        }

        db.session.add_all(
            [
                RequestRevision(**revision_values),
                RequestRevision(**revision_values),
            ]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_request_comment_can_be_created(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A request should support immutable contextual comments."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
        )

        comment = RequestComment(
            purchase_request=request,
            author_id=active_user.id,
            comment_type=CommentType.GENERAL,
            body="Please prioritize this request.",
        )

        db.session.add(comment)
        db.session.commit()

        assert comment.id is not None
        assert comment.author == active_user
        assert comment.comment_type == CommentType.GENERAL
        assert comment in request.comments


def test_empty_request_comment_is_rejected(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """A request comment must contain meaningful text."""
    with app.app_context():
        request = create_purchase_request(
            active_user,
            department,
        )

        comment = RequestComment(
            purchase_request=request,
            author_id=active_user.id,
            body="   ",
        )

        db.session.add(comment)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_user_and_department_relationships_include_requests(
    app: Flask,
    active_user: User,
    department: Department,
) -> None:
    """Requests should be accessible through organizational relationships."""
    with app.app_context():
        stored_user = db.session.get(User, active_user.id)
        stored_department = db.session.get(
            Department,
            department.id,
        )

        assert stored_user is not None
        assert stored_department is not None

        request = create_purchase_request(
            stored_user,
            stored_department,
        )
        db.session.commit()

        assert request in stored_user.purchase_requests
        assert request in stored_department.purchase_requests
