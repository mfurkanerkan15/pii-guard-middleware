from functools import lru_cache
from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PII_GUARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Öneksiz GEMINI_API_KEY
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
    )

    # PII_GUARD_ önekli ayarlar
    gemini_model: str = "gemini-2.5-flash"
    token_min_len: int = 4
    dlp_ner_enabled: bool = True
    ner_score_threshold: float = 0.6
    log_level: str = "INFO"
    log_dir: str = "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
