"""Authentication routes."""

from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from app.auth import auth_bp
from app.auth.forms import LoginForm
from app.extensions import db
from app.models import User


def is_safe_redirect_target(target: str) -> bool:
    """Return whether a redirect remains on the current host."""
    host_url = urlsplit(request.host_url)
    redirect_url = urlsplit(urljoin(request.host_url, target))

    return (
        redirect_url.scheme in {"http", "https"}
        and host_url.netloc == redirect_url.netloc
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate an active application user."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()

        user = db.session.scalar(select(User).where(User.email == normalized_email))

        valid_credentials = (
            user is not None
            and user.is_active
            and user.check_password(form.password.data)
        )

        if not valid_credentials:
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form), 401

        if not login_user(user, remember=form.remember_me.data):
            flash("This account is inactive.", "error")
            return render_template("auth/login.html", form=form), 403

        user.last_login_at = datetime.now(UTC)
        db.session.commit()

        next_url = request.args.get("next")

        if next_url and is_safe_redirect_target(next_url):
            return redirect(next_url)

        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    """End the current authenticated session."""
    logout_user()
    flash("You have been signed out.", "success")

    return redirect(url_for("auth.login"))
