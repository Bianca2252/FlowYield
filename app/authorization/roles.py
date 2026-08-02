"""Application role definitions."""

from enum import StrEnum


class RoleName(StrEnum):
    """Define the supported FlowYield application roles."""

    ADMINISTRATOR = "ADMINISTRATOR"
    REQUESTER = "REQUESTER"
    MANAGER_APPROVER = "MANAGER_APPROVER"
    FINANCE_APPROVER = "FINANCE_APPROVER"
    IT_REVIEWER = "IT_REVIEWER"
    DIRECTOR_APPROVER = "DIRECTOR_APPROVER"
    PROCESS_MANAGER = "PROCESS_MANAGER"
    AUDITOR = "AUDITOR"
    EXECUTIVE_VIEWER = "EXECUTIVE_VIEWER"
