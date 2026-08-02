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


class RequestValidationError(WorkflowError, ValueError):
    """Raised when a purchase request is incomplete or invalid."""


class InvalidTransitionError(WorkflowError, ValueError):
    """Raised when the request cannot enter the requested state."""


class ApprovalDecisionError(WorkflowError, ValueError):
    """Raised when an approval decision cannot be recorded."""


class UnauthorizedDecisionError(ApprovalDecisionError):
    """Raised when a user cannot decide the requested workflow step."""


class DecisionCommentRequiredError(ApprovalDecisionError):
    """Raised when a negative decision has no explanation."""
