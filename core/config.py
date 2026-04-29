from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str

    # Postgres
    database_url: str

    # Redis
    redis_url: str

    # ChromaDB
    chroma_persist_path: str = "./chroma_data"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
