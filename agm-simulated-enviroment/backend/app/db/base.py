from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from app.core.config import settings

# Validar que DATABASE_URL apunte a Supabase (no localhost)
# Esta validación es redundante con la de config.py pero proporciona un mensaje claro
# si alguien modifica DATABASE_URL después de la inicialización
if "localhost" in settings.DATABASE_URL.lower() or "127.0.0.1" in settings.DATABASE_URL.lower():
    raise ValueError(
        "DATABASE_URL no puede apuntar a localhost. "
        "Este proyecto solo soporta Supabase. "
        "Por favor, configura DATABASE_URL con la connection string de Supabase. "
        "Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
    )

# Crear engine asíncrono
# Nota: asyncpg requiere que la URL use postgresql+asyncpg://
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(
    database_url,
    echo=False,  # Cambiar a True para debug SQL
    future=True,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=3600,  # Reciclar conexiones cada hora
    connect_args={
        "server_settings": {
            "application_name": "agm_desk_ai_backend",
        },
        "command_timeout": 60,  # Timeout de 60 segundos
    },
)

# Crear sessionmaker asíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base declarativa para modelos
class Base(DeclarativeBase):
    pass


# Dependency injection para FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

