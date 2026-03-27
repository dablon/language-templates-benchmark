"""
Application Configuration

Loads configuration from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    """Application settings."""

    # Server
    port: int = 3003
    host: str = "0.0.0.0"
    log_level: str = "info"
    environment: str = "production"

    # CORS
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    # Application
    app_name: str = "python-template"
    debug: bool = False


def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        port=int(os.getenv("PORT", "3003")),
        host=os.getenv("HOST", "0.0.0.0"),
        log_level=os.getenv("LOG_LEVEL", "info"),
        environment=os.getenv("ENVIRONMENT", "production"),
        app_name=os.getenv("APP_NAME", "python-template"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    )


# Global settings instance
settings = get_settings()
