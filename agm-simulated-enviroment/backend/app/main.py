from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.routers import app_amerika, app_domain, service_desk
from app.core.exceptions import (
    RequestNotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ValidationError,
    create_error_response,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

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
            "La solicitud solicitada no existe o no tienes permisos para accederla",
            str(exc),
        ),
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content=create_error_response(
            "unauthorized",
            "No autorizado",
            str(exc),
        ),
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content=create_error_response(
            "forbidden",
            "Acceso denegado",
            str(exc),
        ),
    )


@app.exception_handler(ValidationError)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            "validation_error",
            "Error de validación",
            str(exc),
        ),
    )


@app.get("/")
async def root():
    return {"message": "Welcome to AGM Desk AI Backend"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }

