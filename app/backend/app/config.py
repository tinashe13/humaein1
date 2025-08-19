from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = "dev"
    cors_allow_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # DB (MongoDB)
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "claims_pipeline"

    # Ingestion
    max_upload_mb: int = 50
    eligibility_reference_date: date = date(2025, 7, 30)
    classifier_mode: str = "rules+heuristic"  # rules | heuristic | mock-llm | rules+heuristic

    # Auth
    auth_enabled: bool = False
    dev_token: str = "devtoken"

    # Files
    data_dir: str = "app/data"
    artifacts_dir: str = "artifacts"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


