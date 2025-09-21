"""Core configuration settings for ReskPoints."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    
    # Database settings
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL for general data"
    )
    TIMESCALE_URL: Optional[str] = Field(
        default=None,
        description="TimescaleDB URL for metrics storage"
    )
    CLICKHOUSE_URL: Optional[str] = Field(
        default=None,
        description="ClickHouse URL for analytics"
    )
    
    # Cache settings
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching"
    )
    
    # Monitoring settings
    PROMETHEUS_PORT: int = Field(
        default=9090,
        description="Prometheus metrics port"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")
    
    # Authentication settings
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=60, description="JWT token expiration")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute")
    
    # External integrations
    ALERT_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Webhook URL for alerts"
    )


# Global settings instance
settings = Settings()