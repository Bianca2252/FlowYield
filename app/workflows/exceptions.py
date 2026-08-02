"""Workflow domain exceptions."""


class WorkflowError(Exception):
    """Base exception for workflow business failures."""


class WorkflowConfigurationError(WorkflowError, ValueError):
    """Raised when workflow configuration data is invalid."""


class ApprovalPathError(WorkflowError, ValueError):
    """Raised when an approval path cannot be generated."""
