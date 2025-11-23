"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "AI Resume Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/resume_analyzer"
    )
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = Field(default="change-this-secret-key")
    JWT_SECRET_KEY: str = Field(default="change-this-jwt-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    ALLOW_CREDENTIALS: bool = True

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt"
    UPLOAD_DIR: str = "./uploads"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions into a list."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    # NLP Models
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    USE_GPU: bool = False
    BATCH_SIZE: int = 32

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Email (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@example.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
