"""
Configuration module with environment variable validation.
Provides centralized settings management for the application.
"""
import os
from typing import List, Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """

    # Application
    APP_NAME: str = "Blog Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str]

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # Security
    BCRYPT_ROUNDS: int = 12

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY length for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL uses asyncpg for async support."""
        if "postgresql://" in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
            logger.warning("Converted DATABASE_URL to use asyncpg driver")
        elif "postgresql+asyncpg://" not in v:
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// for async support")
        return v


try:
    settings = Settings()
    logger.info(f"Configuration loaded successfully for environment: {settings.ENVIRONMENT}")
except Exception as e:
    logger.error(f"Failed to load configuration: {str(e)}")
    raise
