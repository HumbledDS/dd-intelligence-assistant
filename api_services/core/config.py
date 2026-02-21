"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # GCP
    GCP_PROJECT_ID: str = "your-project-id"
    GCP_REGION: str = "europe-west1"

    # Database (Cloud SQL via Auth Proxy locally, Unix socket in Cloud Run)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/dd_intelligence"

    # Cache (in-process via cachetools — no Redis needed)
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes L1
    CACHE_MAX_SIZE: int = 500

    # Cloud Storage
    GCS_RAW_BUCKET: str = "dd-raw-data"
    GCS_PROCESSED_BUCKET: str = "dd-processed"

    # Gemini API (pay-per-use, AI Studio)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_CHAT: str = "gemini-1.5-flash"
    GEMINI_MODEL_EMBED: str = "text-embedding-004"

    # French Data APIs
    DINUM_API_URL: str = "https://recherche-entreprises.api.gouv.fr"
    INSEE_API_KEY: str = ""
    INFOGREFFE_API_KEY: str = ""
    BODACC_API_URL: str = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1"
    NEWS_API_KEY: str = ""

    # App
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
