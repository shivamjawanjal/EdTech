from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    # Media Storage Configuration
    STORAGE_PROVIDER: str = "mock"
    S3_BUCKET_NAME: str = "edtech-media-dev"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = "auto"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
