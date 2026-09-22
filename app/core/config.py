from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Knowledge API"
    environment: str = "development"
    debug: bool = False

    database_url: str
    test_database_url: str
    storage_path: str = "storage/documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_upload_size: int = 10 * 1024 * 1024  # 10 MB

    max_processing_attempts: int = 3
    processing_timeout_minutes: int = 15

    allowed_extensions: set[str] = {".pdf", ".txt"}
    allowed_content_types: set[str] = {
        "application/pdf",
        "text/plain",
    }

settings = Settings()