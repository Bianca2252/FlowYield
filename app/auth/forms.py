"""Authentication forms."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


def normalize_email(value: str | None) -> str:
    """Normalize an email address before validation."""
    return value.strip().lower() if value else ""


class LoginForm(FlaskForm):
    """Collect user login credentials."""

    email = StringField(
        "Email",
        filters=[normalize_email],
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")
