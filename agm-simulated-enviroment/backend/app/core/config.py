from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AGM Desk AI Backend"
    VERSION: str = "0.1.0"
    DATABASE_URL: str

    # API Key authentication for action endpoints
    API_SECRET_KEY: str

    # CORS configuration
    CORS_ORIGINS: str  # Comma-separated list of allowed origins

    # Supabase configuration (requerido - solo Supabase es soportado)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET: str  # JWT Secret para validar tokens (obtener desde Dashboard > Settings > API > JWT Secret)
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Redis configuration (opcional - para cache)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False  # Por defecto deshabilitado, habilitar si Redis está disponible

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Valida que DATABASE_URL no apunte a localhost (PostgreSQL local no está soportado)"""
        if "localhost" in v.lower() or "127.0.0.1" in v.lower():
            raise ValueError(
                "DATABASE_URL no puede apuntar a localhost. "
                "Este proyecto solo soporta Supabase. "
                "Por favor, configura DATABASE_URL con la connection string de Supabase. "
                "Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
            )
        if "supabase" not in v.lower():
            raise ValueError(
                "DATABASE_URL debe apuntar a Supabase. "
                "Este proyecto solo soporta Supabase como base de datos. "
                "Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
            )
        return v

    @model_validator(mode="after")
    def validate_supabase_config(self):
        """Valida que las variables de Supabase estén configuradas correctamente"""
        if not self.SUPABASE_URL.startswith("https://"):
            raise ValueError(
                "SUPABASE_URL debe ser una URL válida que comience con https://. "
                "Obtén la URL desde: Supabase Dashboard > Settings > API > Project URL"
            )
        if not self.SUPABASE_ANON_KEY.startswith("eyJ"):
            raise ValueError(
                "SUPABASE_ANON_KEY parece inválida. "
                "Obtén la anon key desde: Supabase Dashboard > Settings > API > anon public key"
            )
        return self


settings = Settings()

