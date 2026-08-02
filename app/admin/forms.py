"""Administration forms."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


def normalize_email(value: str | None) -> str:
    """Normalize an email address before validation."""
    return value.strip().lower() if value else ""


class UserCreateForm(FlaskForm):
    """Collect data required to create an application user."""

    email = StringField(
        "Email",
        filters=[normalize_email],
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )
    first_name = StringField(
        "First name",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    last_name = StringField(
        "Last name",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "Temporary password",
        validators=[
            DataRequired(),
            Length(min=12, max=255),
        ],
    )
    department_id = SelectField(
        "Department",
        coerce=int,
        validators=[DataRequired()],
    )
    manager_id = SelectField(
        "Manager",
        coerce=int,
        validators=[Optional()],
    )
    role_ids = SelectMultipleField(
        "Roles",
        coerce=int,
        validators=[DataRequired()],
    )
    is_active = BooleanField(
        "Active account",
        default=True,
    )
    submit = SubmitField("Create user")


class UserEditForm(FlaskForm):
    """Collect editable application user data."""

    email = StringField(
        "Email",
        filters=[normalize_email],
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )
    first_name = StringField(
        "First name",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    last_name = StringField(
        "Last name",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "New password",
        validators=[
            Optional(),
            Length(min=12, max=255),
        ],
    )
    department_id = SelectField(
        "Department",
        coerce=int,
        validators=[DataRequired()],
    )
    manager_id = SelectField(
        "Manager",
        coerce=int,
        validators=[Optional()],
    )
    role_ids = SelectMultipleField(
        "Roles",
        coerce=int,
        validators=[DataRequired()],
    )
    is_active = BooleanField("Active account")
    submit = SubmitField("Save changes")
