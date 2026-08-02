"""Workflow domain exceptions."""


class WorkflowError(Exception):
    """Base exception for workflow business failures."""


class WorkflowConfigurationError(WorkflowError, ValueError):
    """Raised when workflow configuration data is invalid."""


class ApprovalPathError(WorkflowError, ValueError):
    """Raised when an approval path cannot be generated."""


class ApproverAssignmentError(WorkflowError, ValueError):
    """Raised when an eligible approver cannot be assigned."""


class MissingManagerError(ApproverAssignmentError):
    """Raised when Manager Approval has no configured manager."""


class InactiveApproverError(ApproverAssignmentError):
    """Raised when a required approver is inactive."""


class InvalidApproverRoleError(ApproverAssignmentError):
    """Raised when an approver lacks the required role."""


class SelfApprovalError(ApproverAssignmentError):
    """Raised when a requester would approve their own request."""
