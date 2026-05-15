from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="Asia/Kolkata", alias="TIMEZONE")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    admin_bot_token: str = Field(alias="ADMIN_BOT_TOKEN")
    admin_chat_id: int = Field(alias="ADMIN_CHAT_ID")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    earnkaro_api_token: str = Field(default="", alias="EARNKARO_API_TOKEN")
    earnkaro_base_url: str = Field(
        default="https://ekaro-api.affiliaters.in/api/converter/public",
        alias="EARNKARO_BASE_URL",
    )

    check_interval_minutes: int = Field(default=30, alias="CHECK_INTERVAL_MINUTES")
    max_tracked_products_per_user: int = Field(default=100, alias="MAX_TRACKED_PRODUCTS_PER_USER")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    http_timeout_seconds: int = Field(default=20, alias="HTTP_TIMEOUT_SECONDS")
    user_message_rate_limit: int = Field(default=12, alias="USER_MESSAGE_RATE_LIMIT")
    user_message_rate_window_seconds: int = Field(default=60, alias="USER_MESSAGE_RATE_WINDOW_SECONDS")

    playwright_enabled: bool = Field(default=True, alias="PLAYWRIGHT_ENABLED")
    scrapling_enabled: bool = Field(default=True, alias="SCRAPLING_ENABLED")
    proxy_url: str | None = Field(default=None, alias="PROXY_URL")
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        alias="USER_AGENT",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def normalize_admin_ids(cls, value: str | list[int] | None) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return value

    @property
    def parsed_admin_ids(self) -> set[int]:
        if not self.admin_ids.strip():
            return set()
        return {int(item.strip()) for item in self.admin_ids.split(",") if item.strip().isdigit()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
