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
