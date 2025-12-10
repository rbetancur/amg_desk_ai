import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.db.base import engine
from app.routers import app_amerika, app_domain, service_desk
from app.core.exceptions import (
    RequestNotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ValidationError,
    create_error_response,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)


@app.on_event("startup")
async def validate_startup():
    """Valida la configuración de Supabase al iniciar la aplicación"""
    logger.info("Validando configuración de Supabase...")
    
    # Validar que DATABASE_URL apunte a Supabase
    if "localhost" in settings.DATABASE_URL.lower() or "127.0.0.1" in settings.DATABASE_URL.lower():
        error_msg = (
            "ERROR: DATABASE_URL apunta a localhost. "
            "Este proyecto solo soporta Supabase. "
            "Por favor, configura DATABASE_URL con la connection string de Supabase. "
            "Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if "supabase" not in settings.DATABASE_URL.lower():
        error_msg = (
            "ERROR: DATABASE_URL no apunta a Supabase. "
            "Este proyecto solo soporta Supabase como base de datos. "
            "Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validar variables de Supabase
    if not settings.SUPABASE_URL:
        error_msg = "ERROR: SUPABASE_URL no está configurada. Es requerida para este proyecto."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not settings.SUPABASE_ANON_KEY:
        error_msg = "ERROR: SUPABASE_ANON_KEY no está configurada. Es requerida para este proyecto."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not settings.SUPABASE_JWT_SECRET:
        error_msg = "ERROR: SUPABASE_JWT_SECRET no está configurada. Es requerida para este proyecto."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Intentar conectar a la base de datos
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a Supabase verificada exitosamente")
    except Exception as e:
        error_msg = f"ERROR: No se pudo conectar a Supabase: {str(e)}. Verifica que DATABASE_URL sea correcta."
        logger.error(error_msg)
        raise ConnectionError(error_msg) from e
    
    logger.info("✅ Configuración de Supabase validada correctamente")

# Configurar CORS
origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Registrar routers
app.include_router(app_amerika.router, prefix="/api/apps/amerika", tags=["Amerika"])
app.include_router(app_domain.router, prefix="/api/apps/dominio", tags=["Dominio"])
app.include_router(service_desk.router, prefix="/api/requests", tags=["Service Desk"])


# Exception handlers
@app.exception_handler(RequestNotFoundError)
async def request_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            "request_not_found",
            "La solicitud solicitada no existe o no tienes permisos para accederla.",
            detail=str(exc),
            action_suggestion="Regresa a la página anterior o verifica que la URL sea correcta.",
        ),
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content=create_error_response(
            "unauthorized",
            "Tu sesión ha expirado o no tienes autorización. Por favor, inicia sesión nuevamente.",
            detail=str(exc),
            action_suggestion="Haz clic en 'Iniciar Sesión' para autenticarte.",
        ),
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content=create_error_response(
            "forbidden",
            "No tienes permisos para realizar esta acción.",
            detail=str(exc),
            action_suggestion="Si necesitas acceso, contacta al administrador del sistema.",
        ),
    )


@app.exception_handler(ValidationError)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            "validation_error",
            "Algunos campos tienen errores. Revisa los campos marcados y corrige la información antes de enviar.",
            detail=str(exc),
            action_suggestion="Verifica que todos los campos requeridos estén completos y tengan el formato correcto.",
        ),
    )


@app.get("/")
async def root():
    return {"message": "Welcome to AGM Desk AI Backend"}


@app.get("/health")
async def health():
    """Health check endpoint que verifica la conexión a Supabase"""
    db_status = "unknown"
    db_error = None
    db_type = "supabase" if "supabase" in settings.DATABASE_URL.lower() else "unknown"
    
    # Verificar que no apunte a localhost
    if "localhost" in settings.DATABASE_URL.lower() or "127.0.0.1" in settings.DATABASE_URL.lower():
        db_status = "misconfigured"
        db_error = "DATABASE_URL apunta a localhost. Este proyecto solo soporta Supabase."
        db_type = "invalid"
    else:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = "disconnected"
            db_error = str(e)
    
    overall_status = "ok" if db_status == "connected" else "degraded"
    
    response = {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "type": db_type,
            "status": db_status,
        }
    }
    
    if db_error:
        response["database"]["error"] = db_error
    
    status_code = 200 if overall_status == "ok" else 503
    return JSONResponse(content=response, status_code=status_code)

