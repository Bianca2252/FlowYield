"""Approval decision forms."""

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import Length, Optional

from app.models import DecisionType


class ApprovalDecisionForm(FlaskForm):
    """Collect an approver's authoritative workflow decision."""

    decision = SelectField(
        "Decision",
        choices=[
            (
                DecisionType.APPROVE.value,
                "Approve",
            ),
            (
                DecisionType.REJECT.value,
                "Reject",
            ),
            (
                DecisionType.RETURN_FOR_CHANGES.value,
                "Return for changes",
            ),
        ],
    )

    comment = TextAreaField(
        "Comment",
        validators=[
            Optional(),
            Length(max=2000),
        ],
    )

    submit = SubmitField("Record decision")
