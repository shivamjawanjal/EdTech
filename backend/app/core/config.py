from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Teacher Learning & Productivity Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database URLs
    DATABASE_URL: str = "postgresql+asyncpg://postgres:@localhost:5432/edtech_dev"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:@localhost:5432/edtech_dev"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:@localhost:5432/edtech_test"
    TEST_SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:@localhost:5432/edtech_test"

    # Pool Configuration (Tailored for ~150 concurrent students)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Security Configuration
    JWT_SECRET_KEY: str = "temporary_dev_secret_key_needs_override_in_prod_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie & CSRF Settings
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"  # "lax", "strict", "none"
    COOKIE_DOMAIN: Optional[str] = None
    CSRF_PROTECTION_ENABLED: bool = True

    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Media Storage Configuration
    STORAGE_PROVIDER: str = "mock"  # "mock", "s3", "r2"
    S3_BUCKET_NAME: str = "edtech-media-dev"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = "auto"
    MEDIA_PUBLIC_BASE_URL: Optional[str] = None

    # Signed URL TTL Configuration (seconds)
    SIGNED_URL_VIDEO_TTL_SECONDS: int = 1800      # 30 minutes for video playback
    SIGNED_URL_DOWNLOAD_TTL_SECONDS: int = 900    # 15 minutes for notes / attachment download
    SIGNED_URL_UPLOAD_TTL_SECONDS: int = 900      # 15 minutes for direct upload tickets

    # Media File Size Limits (bytes)
    MAX_VIDEO_SIZE_BYTES: int = 1610612736        # 1.5 GB for teacher lecture videos
    MAX_NOTE_SIZE_BYTES: int = 52428800           # 50 MB for lecture note PDFs
    MAX_ATTACHMENT_SIZE_BYTES: int = 15728640     # 15 MB for student assignment attachments

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
