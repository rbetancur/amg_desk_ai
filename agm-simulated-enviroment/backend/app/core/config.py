from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AGM Desk AI Backend"
    VERSION: str = "0.1.0"
    DATABASE_URL: str

    # API Key authentication for action endpoints
    API_SECRET_KEY: str

    # CORS configuration
    CORS_ORIGINS: str  # Comma-separated list of allowed origins

    # Supabase configuration (opcional, solo necesario para Supabase)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

