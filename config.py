"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="AsyncFlow Job Processor", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_version: str = Field(default="v1", alias="API_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")
    sqs_queue_url: str = Field(..., alias="SQS_QUEUE_URL")
    sqs_dlq_url: Optional[str] = Field(default=None, alias="SQS_DLQ_URL")
    
    # Worker Configuration
    workers_count: int = Field(default=4, alias="WORKERS_COUNT")
    max_concurrent_jobs: int = Field(default=10, alias="MAX_CONCURRENT_JOBS")
    poll_interval: int = Field(default=5, alias="POLL_INTERVAL")
    visibility_timeout: int = Field(default=300, alias="VISIBILITY_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_delay: int = Field(default=5, alias="RETRY_DELAY")
    retry_backoff_multiplier: int = Field(default=2, alias="RETRY_BACKOFF_MULTIPLIER")
    
    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_key: str = Field(..., alias="API_KEY")
    allowed_hosts: str = Field(default="*", alias="ALLOWED_HOSTS")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ORIGINS"
    )
    
    # Notifications
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(..., alias="SMTP_USER")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    notification_from_email: str = Field(..., alias="NOTIFICATION_FROM_EMAIL")
    notification_from_name: str = Field(
        default="AsyncFlow Notifications",
        alias="NOTIFICATION_FROM_NAME"
    )
    
    # WebSocket
    ws_heartbeat_interval: int = Field(default=30, alias="WS_HEARTBEAT_INTERVAL")
    ws_max_connections: int = Field(default=1000, alias="WS_MAX_CONNECTIONS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # Redis (Optional)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # Job Configuration
    job_timeout: int = Field(default=3600, alias="JOB_TIMEOUT")
    max_job_size_mb: int = Field(default=100, alias="MAX_JOB_SIZE_MB")
    
    # Monitoring (Optional)
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(default=None, alias="DATADOG_API_KEY")
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]
    
    @field_validator("allowed_hosts")
    @classmethod
    def parse_allowed_hosts(cls, v: str) -> List[str]:
        """Parse comma-separated allowed hosts."""
        if v == "*":
            return ["*"]
        return [host.strip() for host in v.split(",")]
    
    @property
    def database_url_async(self) -> str:
        """Convert database URL to async version for asyncpg."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Create cached instance of settings.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
