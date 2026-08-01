"""FlowYield application factory."""

from flask import Flask

from app.config import CONFIG_MAP, INSTANCE_DIR
from app.extensions import db, migrate


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

    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app: Flask) -> None:
    """Register application Blueprints."""
    from app.main import main_bp

    app.register_blueprint(main_bp)
