"""
Router para endpoints de acción de la aplicación Amerika.
Simula las acciones que el Agente AI ejecutará.
"""
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import (
    AmerikaActionRequest,
    AmerikaActionResponse,
    AmerikaPasswordResult,
    AmerikaAccountResult,
)
from app.services.auth_service import get_api_key
from app.services.password_service import generate_password_amerika
from app.core.exceptions import create_error_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/execute-action",
    response_model=AmerikaActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar acción de Amerika",
    description="Ejecuta una acción simulada de la aplicación Amerika (generar contraseña, desbloquear/bloquear cuenta)",
    responses={
        200: {"description": "Acción ejecutada exitosamente"},
        400: {"description": "Request inválido (action_type no reconocido)"},
        401: {"description": "API Key inválida o faltante"},
        422: {"description": "Validación de datos fallida"},
        500: {"description": "Error interno del servidor"},
    },
)
async def execute_action(
    request: AmerikaActionRequest,
    api_key: str = Depends(get_api_key),
) -> AmerikaActionResponse:
    """
    Ejecuta una acción de Amerika.
    
    Acciones soportadas:
    - generate_password: Genera nueva contraseña alfanumérica (10-25 caracteres)
    - unlock_account: Desbloquea cuenta de usuario
    - lock_account: Bloquea cuenta de usuario
    """
    try:
        # Validar action_type
        valid_actions = ["generate_password", "unlock_account", "lock_account"]
        if request.action_type not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    error_code="invalid_action_type",
                    message="El tipo de acción solicitada no es válido.",
                    detail=f"Tipo de acción '{request.action_type}' no válido",
                    action_suggestion="Verifica que la acción sea una de las permitidas: generar contraseña, desbloquear cuenta o bloquear cuenta.",
                ),
            )

        # Simular procesamiento (sleep 2 segundos)
        await asyncio.sleep(2)

        try:
            if request.action_type == "generate_password":
                # Generar contraseña
                try:
                    password = generate_password_amerika()
                except Exception as e:
                    logger.error("Error al generar contraseña", error=str(e), exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=create_error_response(
                            error_code="password_generation_failed",
                            message="No se pudo generar la contraseña. Por favor, intenta nuevamente.",
                            detail=f"Error técnico: {str(e)}",
                            action_suggestion="Tu solicitud será reintentada automáticamente.",
                        ),
                    )
                
                timestamp = datetime.utcnow().isoformat() + "Z"
                
                result = AmerikaPasswordResult(
                    password_length=len(password),
                    generated_at=timestamp,
                )
                
                return AmerikaActionResponse(
                    success=True,
                    action_type=request.action_type,
                    result=result.model_dump(),
                    message="Contraseña generada exitosamente",
                    generated_password=password,
                )

            elif request.action_type in ["unlock_account", "lock_account"]:
                # Determinar estado según acción
                account_status = "unlocked" if request.action_type == "unlock_account" else "locked"
                timestamp = datetime.utcnow().isoformat() + "Z"
                
                result = AmerikaAccountResult(
                    account_status=account_status,
                    action_timestamp=timestamp,
                )
                
                action_message = (
                    "Cuenta desbloqueada exitosamente"
                    if request.action_type == "unlock_account"
                    else "Cuenta bloqueada exitosamente"
                )
                
                return AmerikaActionResponse(
                    success=True,
                    action_type=request.action_type,
                    result=result.model_dump(),
                    message=action_message,
                    generated_password=None,
                )

        except HTTPException:
            # Re-lanzar HTTPException para que FastAPI las maneje
            raise
        except Exception as e:
            logger.error("Error inesperado al ejecutar acción", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="internal_server_error",
                    message="Ocurrió un error inesperado al procesar tu solicitud.",
                    detail=f"Error técnico: {str(e)}",
                    action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
                ),
            )

    except HTTPException:
        # Re-lanzar HTTPException para que FastAPI las maneje
        raise
    except Exception as e:
        # Capturar cualquier otro error inesperado
        logger.error("Error inesperado en execute_action", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="internal_server_error",
                message="Ocurrió un error inesperado al procesar tu solicitud.",
                detail=f"Error técnico: {str(e)}",
                action_suggestion="Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.",
            ),
        )

