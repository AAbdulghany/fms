from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NexTask FMS API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "postgresql+psycopg2://fms:fms@localhost:5432/fms"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Server-side exports (e.g. maintenance report PDF snapshots)
    data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
