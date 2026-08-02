"""FlowYield application factory."""

from flask import Flask

from app.config import CONFIG_MAP, INSTANCE_DIR
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str = "development") -> Flask:
    """Create and configure a FlowYield application instance."""
    if config_name not in CONFIG_MAP:
        raise ValueError(f"Unknown configuration: {config_name}")

    config_class = CONFIG_MAP[config_name]

    if config_name == "production":
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)

    INSTANCE_DIR.mkdir(exist_ok=True)

    initialize_extensions(app)
    register_blueprints(app)
    register_models()
    register_errors(app)
    register_commands(app)

    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        """Load an active user from the authenticated session."""
        try:
            user = db.session.get(User, int(user_id))
        except TypeError, ValueError:
            return None

        if user is None or not user.is_active:
            return None

        return user


def register_blueprints(app: Flask) -> None:
    """Register application Blueprints."""
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.main import main_bp
    from app.requests import requests_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(requests_bp)


def register_models() -> None:
    """Import models so migration tooling can discover them."""
    from app import models  # noqa: F401


def register_errors(app: Flask) -> None:
    """Register application error handlers."""
    from app.errors import register_error_handlers

    register_error_handlers(app)


def register_commands(app: Flask) -> None:
    """Register application CLI commands."""
    from app.commands import register_commands as register_cli_commands

    register_cli_commands(app)


from app.models import User  # noqa: E402
