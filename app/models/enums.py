"""Domain enumeration definitions."""

from enum import StrEnum


class RequestCategory(StrEnum):
    """Define supported purchase request categories."""

    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    IT_SERVICES = "IT_SERVICES"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    PROFESSIONAL_SERVICES = "PROFESSIONAL_SERVICES"
    FACILITIES = "FACILITIES"
    TRAINING = "TRAINING"
    OTHER = "OTHER"


class RequestStatus(StrEnum):
    """Define the lifecycle states of a purchase request."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class CommentType(StrEnum):
    """Define supported purchase request comment types."""

    GENERAL = "GENERAL"
    REQUESTER_RESPONSE = "REQUESTER_RESPONSE"
    APPROVER_NOTE = "APPROVER_NOTE"
    SYSTEM_NOTE = "SYSTEM_NOTE"


class StepType(StrEnum):
    """Define supported workflow approval step types."""

    MANAGER_APPROVAL = "MANAGER_APPROVAL"
    IT_REVIEW = "IT_REVIEW"
    FINANCE_APPROVAL = "FINANCE_APPROVAL"
    DIRECTOR_APPROVAL = "DIRECTOR_APPROVAL"


class WorkflowCycleStatus(StrEnum):
    """Define workflow cycle lifecycle states."""

    ACTIVE = "ACTIVE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


class WorkflowStepStatus(StrEnum):
    """Define workflow step lifecycle states."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class DecisionType(StrEnum):
    """Define authoritative workflow decision values."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_FOR_CHANGES = "RETURN_FOR_CHANGES"


class SLAResult(StrEnum):
    """Define active and completed SLA interpretations."""

    ON_TIME = "ON_TIME"
    APPROACHING_DEADLINE = "APPROACHING_DEADLINE"
    OVERDUE = "OVERDUE"
    COMPLETED_ON_TIME = "COMPLETED_ON_TIME"
    COMPLETED_LATE = "COMPLETED_LATE"
