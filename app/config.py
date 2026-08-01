"""Application configuration classes."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


class BaseConfig:
    """Configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret-key")
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'flowyield.db'}",
    )


class TestingConfig(BaseConfig):
    """Automated test configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    @classmethod
    def validate(cls) -> None:
        """Validate required production environment variables."""
        missing_variables = [
            variable
            for variable in ("SECRET_KEY", "DATABASE_URL")
            if not os.getenv(variable)
        ]

        if missing_variables:
            joined_variables = ", ".join(missing_variables)
            raise RuntimeError(
                "Missing required production environment variables: "
                f"{joined_variables}."
            )


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
