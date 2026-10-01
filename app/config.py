"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # Gemini API
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        "models/gemini-flash-latest",
        alias="GEMINI_MODEL"
    )

    # App configuration
    app_env: str = Field("development", alias="APP_ENV")
    debug: bool = Field(True, alias="DEBUG")

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    output_dir: Path = base_dir / "output"
    knowledge_base_dir: Path = base_dir / "knowledge_base"
    chroma_db_dir: Path = base_dir / "chroma_db"
    uploads_dir: Path = base_dir / "uploads"

    # Model paths
    network_coverage_model_path: Path = Field(
        base_dir / "models" / "network_coverage_model.pkl",
        alias="NETWORK_COVERAGE_MODEL_PATH"
    )
    qos_model_path: Path = Field(
        base_dir / "models" / "qos_model.pkl",
        alias="QOS_MODEL_PATH"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @field_validator("gemini_model")
    @classmethod
    def normalize_gemini_model(cls, value: str) -> str:
        if value and not value.startswith("models/"):
            return f"models/{value}"
        return value


# Global settings instance
settings = Settings()
