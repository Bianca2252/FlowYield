"""Authorization decorators."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import abort
from flask_login import current_user, login_required

from app.authorization.roles import RoleName

ViewFunction = TypeVar(
    "ViewFunction",
    bound=Callable[..., Any],
)


def roles_required(*required_roles: RoleName) -> Callable[[ViewFunction], ViewFunction]:
    """Require the authenticated user to hold at least one specified role."""
    if not required_roles:
        raise ValueError("At least one role must be provided.")

    def decorator(view_function: ViewFunction) -> ViewFunction:
        @wraps(view_function)
        @login_required
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            has_required_role = any(
                current_user.has_role(role.value) for role in required_roles
            )

            if not has_required_role:
                abort(403)

            return view_function(*args, **kwargs)

        return cast(ViewFunction, wrapped_view)

    return decorator
