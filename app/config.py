"""Application configuration classes."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    """Configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret-key")
    TESTING = False


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Automated test configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False

    @classmethod
    def validate(cls) -> None:
        """Validate required production environment variables."""
        if not os.getenv("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be configured in the production environment."
            )


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
