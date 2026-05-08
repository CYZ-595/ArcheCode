"""
Application configuration management.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ArcheCode"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.3

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"

    # Analysis
    MAX_FILE_SIZE_KB: int = 500
    SUPPORTED_EXTENSIONS: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
        ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".hpp",
        ".json", ".yaml", ".yml", ".toml", ".xml",
        ".md", ".txt", ".rst",
        ".html", ".css", ".scss", ".less",
        ".sql", ".graphql", ".proto",
        ".sh", ".bash", ".zsh",
        ".dockerfile", ".docker-compose.yml",
    ]

    # RAG / Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    FAISS_INDEX_PATH: str = "./data/faiss_index"

    # Redis (optional, for caching)
    REDIS_URL: Optional[str] = None

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Database (SQLite by default, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./data/archecode.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


settings = get_settings()
