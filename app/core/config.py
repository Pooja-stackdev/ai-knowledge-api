"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    app_name: str = "AI Knowledge API"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str
    test_database_url: str

    document_storage_path: str = "storage/documents"
    faiss_index_path: str = "storage/faiss/documents.index"

    max_upload_size: int = Field(
        default=30 * 1024 * 1024,
        gt=0,
        description="Maximum allowed document upload size in bytes.",
    )

    max_processing_attempts: int = Field(
        default=3,
        gt=0,
    )

    processing_timeout_minutes: int = Field(
        default=15,
        gt=0,
    )

    allowed_extensions: set[str] = {".pdf", ".txt"}

    allowed_content_types: set[str] = {
        "application/pdf",
        "text/plain",
    }

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = Field(
        default=384,
        gt=0,
    )

    groq_api_key: str
    groq_model: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    retrieval_score_threshold: float = 0.30

    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_retry_delay_seconds: float = 1.0


settings = Settings()
