"""
Configuration settings for DocOps Agent.
"""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    langchain_api_key: str = ""

    # LangSmith
    langchain_tracing_v2: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "docops-agent"

    # Database
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "docops"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # App settings
    app_name: str = "DocOps Agent"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:8501"

    # Processing settings
    confidence_threshold: float = 0.7
    value_threshold: float = 1000.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
