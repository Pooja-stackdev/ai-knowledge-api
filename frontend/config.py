from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_BASE_URL: str = "http://127.0.0.1:8000"
    API_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()