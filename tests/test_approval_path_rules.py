"""Tests for deterministic purchase approval path rules."""

from decimal import Decimal

import pytest
from app.extensions import db
from app.models import (
    RequestCategory,
    StepType,
    User,
    WorkflowConfiguration,
)
from app.workflows.exceptions import WorkflowConfigurationError
from app.workflows.rules import (
    build_approval_path,
    requires_director_approval,
    requires_finance_approval,
    requires_it_review,
)
from flask import Flask


def create_configuration(
    creator: User,
    *,
    low_value_threshold: Decimal = Decimal("1000.00"),
    high_value_threshold: Decimal = Decimal("10000.00"),
    it_review_threshold: Decimal = Decimal("5000.00"),
    it_review_enabled: bool = True,
) -> WorkflowConfiguration:
    """Create a workflow configuration for rule tests."""
    configuration = WorkflowConfiguration(
        version_number=1,
        name="Approval path test configuration",
        low_value_threshold=low_value_threshold,
        high_value_threshold=high_value_threshold,
        it_review_threshold=it_review_threshold,
        it_review_enabled=it_review_enabled,
        created_by_user_id=creator.id,
        is_active=True,
    )

    db.session.add(configuration)
    db.session.flush()

    return configuration


def step_types(path) -> list[StepType]:
    """Return only the ordered step types from a path."""
    return [step.step_type for step in path]


def test_request_below_low_threshold_requires_manager_only(
    app: Flask,
    active_user: User,
) -> None:
    """A request below EUR 1,000 should require Manager only."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("999.99"),
            category=RequestCategory.OFFICE_SUPPLIES,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
        ]


def test_request_at_low_threshold_requires_finance(
    app: Flask,
    active_user: User,
) -> None:
    """Exactly EUR 1,000 should require Manager and Finance."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("1000.00"),
            category=RequestCategory.OFFICE_SUPPLIES,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
        ]


def test_request_at_it_threshold_does_not_require_it_review(
    app: Flask,
    active_user: User,
) -> None:
    """Exactly EUR 5,000 should not require IT Review."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("5000.00"),
            category=RequestCategory.SOFTWARE,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
        ]


@pytest.mark.parametrize(
    "category",
    [
        RequestCategory.SOFTWARE,
        RequestCategory.IT_SERVICES,
    ],
)
def test_it_category_above_it_threshold_inserts_it_review(
    app: Flask,
    active_user: User,
    category: RequestCategory,
) -> None:
    """Qualifying IT categories should include IT Review."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("5000.01"),
            category=category,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
        ]


def test_non_it_category_above_it_threshold_skips_it_review(
    app: Flask,
    active_user: User,
) -> None:
    """A non-IT category should not receive IT Review."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("7200.00"),
            category=RequestCategory.PROFESSIONAL_SERVICES,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
        ]


def test_request_at_high_threshold_does_not_require_director(
    app: Flask,
    active_user: User,
) -> None:
    """Exactly EUR 10,000 should not require Director Approval."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("10000.00"),
            category=RequestCategory.HARDWARE,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
        ]


def test_request_above_high_threshold_requires_director(
    app: Flask,
    active_user: User,
) -> None:
    """A request above EUR 10,000 should include Director Approval."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("10000.01"),
            category=RequestCategory.HARDWARE,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
            StepType.DIRECTOR_APPROVAL,
        ]


def test_high_value_it_request_uses_complete_path(
    app: Flask,
    active_user: User,
) -> None:
    """A high-value IT request should use all approval steps."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("18000.00"),
            category=RequestCategory.IT_SERVICES,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
            StepType.DIRECTOR_APPROVAL,
        ]


def test_disabling_it_rule_removes_it_review(
    app: Flask,
    active_user: User,
) -> None:
    """Disabled IT Review should not generate an IT step."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(
            creator,
            it_review_enabled=False,
        )

        path = build_approval_path(
            amount=Decimal("7200.00"),
            category=RequestCategory.SOFTWARE,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.FINANCE_APPROVAL,
        ]


def test_custom_thresholds_are_used(
    app: Flask,
    active_user: User,
) -> None:
    """Rules should use configuration values rather than hardcoded ones."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(
            creator,
            low_value_threshold=Decimal("2000.00"),
            high_value_threshold=Decimal("15000.00"),
            it_review_threshold=Decimal("8000.00"),
        )

        path = build_approval_path(
            amount=Decimal("15000.00"),
            category=RequestCategory.SOFTWARE,
            configuration=configuration,
        )

        assert step_types(path) == [
            StepType.MANAGER_APPROVAL,
            StepType.IT_REVIEW,
            StepType.FINANCE_APPROVAL,
        ]


def test_generated_steps_have_sequential_numbers(
    app: Flask,
    active_user: User,
) -> None:
    """Generated steps should have deterministic sequence numbers."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("18000.00"),
            category=RequestCategory.SOFTWARE,
            configuration=configuration,
        )

        assert [step.sequence_number for step in path] == [1, 2, 3, 4]


def test_generated_steps_include_rule_explanations(
    app: Flask,
    active_user: User,
) -> None:
    """Every generated step should explain why it was included."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        path = build_approval_path(
            amount=Decimal("7200.00"),
            category=RequestCategory.SOFTWARE,
            configuration=configuration,
        )

        assert all(step.reason_for_inclusion for step in path)
        assert "every purchase request" in path[0].reason_for_inclusion
        assert "SOFTWARE" in path[1].reason_for_inclusion
        assert "5000.00" in path[1].reason_for_inclusion


def test_zero_amount_is_rejected(
    app: Flask,
    active_user: User,
) -> None:
    """A zero amount should not generate a workflow path."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        with pytest.raises(
            WorkflowConfigurationError,
            match="greater than zero",
        ):
            build_approval_path(
                amount=Decimal("0.00"),
                category=RequestCategory.HARDWARE,
                configuration=configuration,
            )


def test_invalid_threshold_order_is_rejected(
    app: Flask,
    active_user: User,
) -> None:
    """Invalid configuration thresholds should fail clearly."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)

        configuration = WorkflowConfiguration(
            version_number=1,
            name="Invalid configuration",
            low_value_threshold=Decimal("10000.00"),
            high_value_threshold=Decimal("1000.00"),
            it_review_threshold=Decimal("5000.00"),
            created_by_user_id=creator.id,
        )

        with pytest.raises(
            WorkflowConfigurationError,
            match="lower than",
        ):
            build_approval_path(
                amount=Decimal("5000.00"),
                category=RequestCategory.HARDWARE,
                configuration=configuration,
            )


def test_rule_helper_functions_use_exact_boundaries(
    app: Flask,
    active_user: User,
) -> None:
    """Rule helper functions should preserve documented boundaries."""
    with app.app_context():
        creator = db.session.get(User, active_user.id)
        configuration = create_configuration(creator)

        assert (
            requires_finance_approval(
                amount=Decimal("1000.00"),
                configuration=configuration,
            )
            is True
        )

        assert (
            requires_director_approval(
                amount=Decimal("10000.00"),
                configuration=configuration,
            )
            is False
        )

        assert (
            requires_it_review(
                amount=Decimal("5000.00"),
                category=RequestCategory.SOFTWARE,
                configuration=configuration,
            )
            is False
        )
