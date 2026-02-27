from pydantic_settings import BaseSettings
from typing import Optional
import yaml
from pathlib import Path


class Settings(BaseSettings):
    # App settings
    app_name: str = "PayWise"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database (SQLite for dev, PostgreSQL for prod)
    database_url: str = "sqlite:///./paywise.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # JWT Auth
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Firebase
    firebase_project_id: Optional[str] = None
    firebase_private_key_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    firebase_client_id: Optional[str] = None

    # Google
    google_places_api_key: Optional[str] = None

    # Gemini
    gemini_api_key: Optional[str] = None
    llm_model: str = "gemini-2.0-flash"

    # LLM Search providers (for restaurant offers)
    llm_search_provider: str = "perplexity"  # "perplexity" or "tavily"
    perplexity_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @classmethod
    def load_yaml_config(cls) -> dict:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}


settings = Settings()
