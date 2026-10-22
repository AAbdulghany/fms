from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ENVS = ("development", "pilot", "production")
# Deprecated spellings still accepted from env files on existing servers.
_APP_ENV_ALIASES = {"demo": "pilot", "dev": "development", "prod": "production"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Orbit API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "postgresql+psycopg2://fms:fms@localhost:9432/fms_local"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # development | pilot | production — controls license freeze bypass and pilot reset
    app_env: str = "development"
    # Server-side exports (e.g. maintenance report PDF snapshots)
    data_dir: str = "data"
    # A2 sticker defaults — size_mm is side (A) or width (C); design a|c
    asset_label_size_mm: float = 70.0
    asset_label_design: str = "a"

    @field_validator("app_env", mode="before")
    @classmethod
    def _normalize_app_env(cls, value: object) -> str:
        env = str(value or "development").strip().lower()
        env = _APP_ENV_ALIASES.get(env, env)
        if env not in APP_ENVS:
            raise ValueError(f"APP_ENV must be one of {', '.join(APP_ENVS)} (got {value!r})")
        return env

    @property
    def is_pilot(self) -> bool:
        return self.app_env == "pilot"

    @property
    def bypasses_license(self) -> bool:
        return self.app_env in ("development", "pilot")


@lru_cache
def get_settings() -> Settings:
    return Settings()
