"""Deterministic purchase approval path rules."""

from dataclasses import dataclass
from decimal import Decimal

from app.models import (
    RequestCategory,
    StepType,
    WorkflowConfiguration,
)
from app.workflows.exceptions import WorkflowConfigurationError

IT_REVIEW_CATEGORIES = {
    RequestCategory.SOFTWARE,
    RequestCategory.IT_SERVICES,
}


@dataclass(frozen=True, slots=True)
class ApprovalPathStep:
    """Describe one required step in an approval path."""

    step_type: StepType
    sequence_number: int
    reason_for_inclusion: str


def validate_rule_inputs(
    *,
    amount: Decimal,
    category: RequestCategory,
    configuration: WorkflowConfiguration,
) -> None:
    """Validate inputs before calculating an approval path."""
    if amount <= 0:
        raise WorkflowConfigurationError(
            "The requested amount must be greater than zero."
        )

    if configuration.low_value_threshold <= 0:
        raise WorkflowConfigurationError(
            "The low-value threshold must be greater than zero."
        )

    if configuration.high_value_threshold <= 0:
        raise WorkflowConfigurationError(
            "The high-value threshold must be greater than zero."
        )

    if configuration.it_review_threshold <= 0:
        raise WorkflowConfigurationError(
            "The IT Review threshold must be greater than zero."
        )

    if configuration.low_value_threshold >= configuration.high_value_threshold:
        raise WorkflowConfigurationError(
            "The low-value threshold must be lower than the high-value threshold."
        )

    if not isinstance(category, RequestCategory):
        raise WorkflowConfigurationError("The request category is not supported.")


def requires_it_review(
    *,
    amount: Decimal,
    category: RequestCategory,
    configuration: WorkflowConfiguration,
) -> bool:
    """Return whether a request requires IT Review."""
    return (
        configuration.it_review_enabled
        and category in IT_REVIEW_CATEGORIES
        and amount > configuration.it_review_threshold
    )


def requires_finance_approval(
    *,
    amount: Decimal,
    configuration: WorkflowConfiguration,
) -> bool:
    """Return whether a request requires Finance Approval."""
    return amount >= configuration.low_value_threshold


def requires_director_approval(
    *,
    amount: Decimal,
    configuration: WorkflowConfiguration,
) -> bool:
    """Return whether a request requires Director Approval."""
    return amount > configuration.high_value_threshold


def build_approval_path(
    *,
    amount: Decimal,
    category: RequestCategory,
    configuration: WorkflowConfiguration,
) -> list[ApprovalPathStep]:
    """Build the ordered approval path for a purchase request."""
    validate_rule_inputs(
        amount=amount,
        category=category,
        configuration=configuration,
    )

    step_definitions: list[tuple[StepType, str]] = [
        (
            StepType.MANAGER_APPROVAL,
            "Manager Approval is required for every purchase request.",
        )
    ]

    if requires_it_review(
        amount=amount,
        category=category,
        configuration=configuration,
    ):
        step_definitions.append(
            (
                StepType.IT_REVIEW,
                (
                    "IT Review is required because the request category "
                    f"is {category.value} and the amount exceeds "
                    f"EUR {configuration.it_review_threshold:.2f}."
                ),
            )
        )

    if requires_finance_approval(
        amount=amount,
        configuration=configuration,
    ):
        step_definitions.append(
            (
                StepType.FINANCE_APPROVAL,
                (
                    "Finance Approval is required because the amount "
                    f"is at least EUR "
                    f"{configuration.low_value_threshold:.2f}."
                ),
            )
        )

    if requires_director_approval(
        amount=amount,
        configuration=configuration,
    ):
        step_definitions.append(
            (
                StepType.DIRECTOR_APPROVAL,
                (
                    "Director Approval is required because the amount "
                    f"exceeds EUR "
                    f"{configuration.high_value_threshold:.2f}."
                ),
            )
        )

    return [
        ApprovalPathStep(
            step_type=step_type,
            sequence_number=sequence_number,
            reason_for_inclusion=reason,
        )
        for sequence_number, (step_type, reason) in enumerate(
            step_definitions,
            start=1,
        )
    ]
