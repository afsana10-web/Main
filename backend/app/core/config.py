"""
PARAKH backend configuration.

All secrets/config come from environment variables (.env). Nothing here is
hard-coded into frontend code. See .env.example for the full list.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PARAKH"
    PROJECT_TAGLINE: str = "Scan. Analyse. Verify."
    API_V1_PREFIX: str = "/api"

    # Database - defaults to local SQLite so the prototype runs out of the box.
    # For a real deployment, set DATABASE_URL to a PostgreSQL DSN, e.g.:
    # postgresql+psycopg2://parakh:password@localhost:5432/parakh
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./parakh.db"
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_ENV")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # CORS - restrict in production; wide open here for the mobile app + dashboard demo
    CORS_ORIGINS: list[str] = ["*"]

    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    REPORT_DIR: str = os.getenv("REPORT_DIR", "generated_reports")

    # OCR
    TESSERACT_CMD: str | None = os.getenv("TESSERACT_CMD")  # None = use system PATH
    OCR_LOW_CONFIDENCE_THRESHOLD: float = 60.0  # below this -> NEEDS_VERIFICATION

    # Rules engine
    RULES_CONFIG_PATH: str = os.getenv(
        "RULES_CONFIG_PATH", "../compliance-rules/rules.json"
    )
    CURRENT_RULESET_VERSION: str = "LMPC-2011-R1"

    # Demo mode
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
