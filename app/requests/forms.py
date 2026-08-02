"""Purchase request forms."""

from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import Length, NumberRange, Optional

from app.models import RequestCategory


class PurchaseRequestDraftForm(FlaskForm):
    """Collect editable purchase request draft data."""

    title = StringField(
        "Request title",
        validators=[
            Optional(),
            Length(max=200),
        ],
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()],
    )

    business_justification = TextAreaField(
        "Business justification",
        validators=[Optional()],
    )

    category = SelectField(
        "Category",
        choices=[
            ("", "Select a category"),
            *[
                (
                    category.value,
                    category.value.replace("_", " ").title(),
                )
                for category in RequestCategory
            ],
        ],
        validators=[Optional()],
    )

    supplier = StringField(
        "Supplier",
        validators=[
            Optional(),
            Length(max=200),
        ],
    )

    requested_amount = DecimalField(
        "Requested amount",
        places=2,
        validators=[
            Optional(),
            NumberRange(
                min=Decimal("0.01"),
                message="The requested amount must be greater than zero.",
            ),
        ],
    )

    expected_purchase_date = DateField(
        "Expected purchase date",
        validators=[Optional()],
    )

    submit = SubmitField("Save draft")


class PurchaseRequestSubmissionForm(FlaskForm):
    """Confirm submission of a completed purchase request."""

    submit = SubmitField("Submit request")
