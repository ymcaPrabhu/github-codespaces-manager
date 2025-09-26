"""
Configuration management for GitHub Codespaces Manager Web API
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Database configuration
    DATABASE_URL: str = "sqlite:///./codespaces_web.db"

    # GitHub CLI configuration
    GITHUB_CLI_PATH: str = "gh"

    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL: int = 30

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # File paths
    STATIC_FILES_DIR: str = "./static"
    TEMPLATES_DIR: str = "./templates"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()