"""
Router para endpoints CRUD de Mesa de Servicio.
"""
import logging
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, DatabaseError
import asyncpg
from app.db.base import get_db
from app.models.entities import Request, Category
from app.models.schemas import (
    RequestCreate,
    RequestResponse,
    RequestUpdate,
    PaginationParams,
    PaginatedResponse,
    PaginationMeta,
)
from app.services.auth_service import get_current_user
from app.services.validation_service import validate_state_transition
from app.core.exceptions import (
    RequestNotFoundError,
    ForbiddenError,
    ValidationError,
    create_error_response,
)

router = APIRouter()

# Cache simple en memoria para categorías válidas
_valid_categories_cache: dict[int, bool] = {}


async def verify_category_exists(
    session: AsyncSession,
    codcategoria: int,
) -> bool:
    """
    Verifica si una categoría existe en la BD.
    Usa cache en memoria para optimizar.
    """
    # Verificar cache primero
    if codcategoria in _valid_categories_cache:
        return _valid_categories_cache[codcategoria]
    
    # Consultar BD
    result = await session.execute(
        select(Category).where(Category.codcategoria == codcategoria)
    )
    category = result.scalar_one_or_none()
    
    exists = category is not None
    _valid_categories_cache[codcategoria] = exists
    
    return exists


@router.get(
    "",
    response_model=PaginatedResponse[RequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar solicitudes",
    description="Lista las solicitudes del usuario autenticado con paginación",
    responses={
        200: {"description": "Lista de solicitudes obtenida exitosamente"},
        401: {"description": "Token JWT inválido, expirado o faltante"},
    },
)
async def list_requests(
    pagination: Annotated[PaginationParams, Query()] = PaginationParams(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RequestResponse]:
    """
    Lista las solicitudes del usuario autenticado con paginación.
    """
    try:
        ususolicita = current_user["ususolicita"]
        
        # Calcular total antes de aplicar limit/offset
        count_result = await db.execute(
            select(func.count()).select_from(Request).where(
                Request.ususolicita == ususolicita
            )
        )
        total = count_result.scalar() or 0
        
        # Aplicar limit máximo de 100
        limit = min(pagination.limit, 100)
        offset = pagination.offset
        
        # Obtener solicitudes
        result = await db.execute(
            select(Request)
            .where(Request.ususolicita == ususolicita)
            .order_by(Request.fesolicita.desc())
            .limit(limit)
            .offset(offset)
        )
        requests = result.scalars().all()
        
        # Calcular has_more
        has_more = (offset + limit) < total
        
        # Si no hay solicitudes, devolver una respuesta vacía exitosa
        return PaginatedResponse(
            items=[RequestResponse.model_validate(req) for req in requests],
            pagination=PaginationMeta(
                total=total,
                limit=limit,
                offset=offset,
                has_more=has_more,
            ),
        )
    except Exception as e:
        # Log del error para debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al listar solicitudes para usuario {current_user.get('ususolicita', 'unknown')}: {str(e)}", exc_info=True)
        
        # Re-lanzar HTTPException para que FastAPI las maneje correctamente
        if isinstance(e, HTTPException):
            raise
        
        # Detectar errores de conexión a la base de datos
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        # Detectar errores de SQLAlchemy
        is_db_error = (
            isinstance(e, (OperationalError, DatabaseError)) or
            isinstance(e.__cause__, (OperationalError, DatabaseError)) or
            isinstance(e.__cause__, asyncpg.exceptions.PostgresError) or
            isinstance(e.__cause__, asyncpg.exceptions.InvalidPasswordError) or
            isinstance(e.__cause__, asyncpg.exceptions.ConnectionDoesNotExistError) or
            "connection" in error_str or
            "database" in error_str or
            "postgres" in error_str or
            "asyncpg" in error_str or
            "connection refused" in error_str or
            "errno 61" in error_str or
            "timeout" in error_str or
            "could not connect" in error_str or
            "authentication failed" in error_str or
            "password authentication failed" in error_str
        )
        
        if is_db_error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=create_error_response(
                    error_code="database_unavailable",
                    message="El servicio no está disponible temporalmente. Estamos trabajando para solucionarlo.",
                    detail=f"Error de conexión a base de datos: {str(e)}",
                    action_suggestion="Intenta nuevamente en unos minutos.",
                ),
            )
        
        # Para otros errores, devolver un error 500 con mensaje genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="internal_server_error",
                message="Ocurrió un error al obtener las solicitudes.",
                detail=f"Error técnico: {str(e)}",
                action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
            ),
        )


@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud",
    description="Crea una nueva solicitud de mesa de servicio",
    responses={
        201: {"description": "Solicitud creada exitosamente"},
        401: {"description": "Token JWT inválido, expirado o faltante"},
        422: {"description": "Validación de datos fallida (categoría no existe, description excede 4000 caracteres)"},
    },
)
async def create_request(
    request_data: RequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """
    Crea una nueva solicitud de mesa de servicio.
    """
    ususolicita = current_user["ususolicita"]
    
    try:
        # Verificar que la categoría existe
        category_exists = await verify_category_exists(db, request_data.codcategoria)
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=create_error_response(
                    error_code="category_not_found",
                    message=f"La categoría seleccionada no existe.",
                    detail=f"Categoría {request_data.codcategoria} no existe",
                    action_suggestion="Selecciona una categoría válida de la lista disponible.",
                ),
            )
        
        # Crear nueva solicitud
        new_request = Request(
            codcategoria=request_data.codcategoria,
            description=request_data.description,
            ususolicita=ususolicita,
            codestado=1,  # PENDIENTE por defecto
            fesolicita=datetime.utcnow(),
        )
        
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
        
        return RequestResponse.model_validate(new_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error inesperado al crear solicitud", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="internal_server_error",
                message="Ocurrió un error al crear la solicitud.",
                detail=f"Error técnico: {str(e)}",
                action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
            ),
        )


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener solicitud",
    description="Obtiene una solicitud específica (solo si pertenece al usuario)",
    responses={
        200: {"description": "Solicitud obtenida exitosamente"},
        401: {"description": "Token JWT inválido, expirado o faltante"},
        403: {"description": "Acceso denegado (solicitud no pertenece al usuario)"},
        404: {"description": "Solicitud no encontrada"},
    },
)
async def get_request(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """
    Obtiene una solicitud específica.
    Solo permite acceso si la solicitud pertenece al usuario autenticado.
    """
    try:
        ususolicita = current_user["ususolicita"]
        
        result = await db.execute(
            select(Request).where(Request.codpeticiones == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    error_code="request_not_found",
                    message="La solicitud solicitada no existe o no tienes permisos para accederla.",
                    detail=f"Solicitud {request_id} no encontrada",
                    action_suggestion="Regresa a la página anterior o verifica que la URL sea correcta.",
                ),
            )
        
        if request.ususolicita != ususolicita:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    error_code="forbidden",
                    message="No tienes permisos para acceder a esta solicitud.",
                    detail="Solicitud no pertenece al usuario autenticado",
                    action_suggestion="Solo puedes acceder a tus propias solicitudes.",
                ),
            )
        
        return RequestResponse.model_validate(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error inesperado al obtener solicitud", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="internal_server_error",
                message="Ocurrió un error al obtener la solicitud.",
                detail=f"Error técnico: {str(e)}",
                action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
            ),
        )


@router.patch(
    "/{request_id}",
    response_model=RequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar solicitud",
    description="Actualiza una solicitud (solo si pertenece al usuario, campos limitados)",
    responses={
        200: {"description": "Solicitud actualizada exitosamente"},
        401: {"description": "Token JWT inválido, expirado o faltante"},
        403: {"description": "Acceso denegado (solicitud no pertenece al usuario)"},
        404: {"description": "Solicitud no encontrada"},
        422: {"description": "Validación de datos fallida (transición de estado no permitida)"},
    },
)
async def update_request(
    request_id: int,
    request_data: RequestUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """
    Actualiza una solicitud.
    Solo permite actualizar campos específicos y solo si la solicitud pertenece al usuario.
    """
    try:
        ususolicita = current_user["ususolicita"]
        
        result = await db.execute(
            select(Request).where(Request.codpeticiones == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    error_code="request_not_found",
                    message="La solicitud solicitada no existe o no tienes permisos para accederla.",
                    detail=f"Solicitud {request_id} no encontrada",
                    action_suggestion="Regresa a la página anterior o verifica que la URL sea correcta.",
                ),
            )
        
        if request.ususolicita != ususolicita:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    error_code="forbidden",
                    message="No tienes permisos para actualizar esta solicitud.",
                    detail="Solicitud no pertenece al usuario autenticado",
                    action_suggestion="Solo puedes actualizar tus propias solicitudes.",
                ),
            )
        
        # Validar transición de estado si se actualiza codestado
        if request_data.codestado is not None:
            current_state = request.codestado or 1
            if not validate_state_transition(current_state, request_data.codestado):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=create_error_response(
                        error_code="invalid_state_transition",
                        message="La transición de estado solicitada no está permitida.",
                        detail=f"Transición de estado no permitida: {current_state} → {request_data.codestado}",
                        action_suggestion="Verifica que la transición de estado sea válida. Los estados solo pueden avanzar de Pendiente → En Trámite → Solucionado.",
                    ),
                )
            request.codestado = request_data.codestado
        
        # Actualizar otros campos permitidos
        if request_data.solucion is not None:
            request.solucion = request_data.solucion
        
        if request_data.fesolucion is not None:
            request.fesolucion = request_data.fesolucion
        
        if request_data.codusolucion is not None:
            request.codusolucion = request_data.codusolucion
        
        if request_data.feccierre is not None:
            request.feccierre = request_data.feccierre
        
        if request_data.ai_classification_data is not None:
            request.ai_classification_data = request_data.ai_classification_data
        
        await db.commit()
        await db.refresh(request)
        
        return RequestResponse.model_validate(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error inesperado al actualizar solicitud", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="internal_server_error",
                message="Ocurrió un error al actualizar la solicitud.",
                detail=f"Error técnico: {str(e)}",
                action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
            ),
        )

