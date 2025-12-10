"""Configuración centralizada del Agente AI usando pydantic-settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuración del Agente AI cargada desde variables de entorno"""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Backend FastAPI Configuration
    BACKEND_URL: str = "http://localhost:8000"
    API_SECRET_KEY: str
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Recomendado para PoC (más económico y rápido)
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_TOKENS: int = 500
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    
    # Rate Limiting Configuration
    ENABLE_RATE_LIMITING: bool = True  # Habilitar/deshabilitar rate limiting (configurable via .env)
    MAX_REQUESTS_PER_USER: int = 5  # Número máximo de solicitudes por usuario en ventana de tiempo
    RATE_LIMIT_WINDOW_HOURS: int = 24  # Ventana de tiempo en horas para rate limiting
    MAX_REQUEST_AGE_HOURS: Optional[int] = None  # Opcional: horas máximas de antigüedad para procesar
    
    # Validation Configuration
    MIN_DESCRIPTION_LENGTH: int = 10
    MAX_DESCRIPTION_LENGTH: int = 4000
    
    # Security Filters Configuration
    ENABLE_SECURITY_FILTERS: bool = True
    PROMPT_INJECTION_KEYWORDS: str = "ignore,actúa,ejecuta,revela,bypass,override,ignora,ejecutar,revelar"
    DANGEROUS_INSTRUCTION_PATTERNS: str = "debes hacer,necesito que hagas,por favor ejecuta,debes,necesitas,tienes que"
    MALICIOUS_CONTENT_KEYWORDS: str = ""  # Opcional: palabras clave adicionales de contenido malicioso
    
    # Prompt Optimization Configuration
    USE_FEW_SHOT_ALWAYS: bool = False  # Si True, siempre usa few-shot. Si False, usa few-shot solo cuando sea necesario
    FEW_SHOT_THRESHOLD_DESCRIPTION_LENGTH: int = 20  # Longitud mínima de descripción para considerar simple (sin few-shot)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Valida variables críticas al inicializar"""
        super().__init__(**kwargs)
        self._validate_critical_variables()
    
    def _validate_critical_variables(self):
        """Valida que todas las variables críticas estén presentes"""
        critical_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "BACKEND_URL",
            "API_SECRET_KEY",
            "GEMINI_API_KEY",
        ]
        missing = []
        for var in critical_vars:
            if not getattr(self, var, None):
                missing.append(var)
        
        if missing:
            raise ValueError(
                f"Variables críticas faltantes: {', '.join(missing)}. "
                "Por favor, configúralas en el archivo .env"
            )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retorna instancia singleton de Settings"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

