"""
Router para endpoints de acción del dominio corporativo.
Simula las acciones que el Agente AI ejecutará.
"""
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import (
    DominioActionRequest,
    DominioActionResponse,
    DominioFindUserResult,
    DominioPasswordResult,
    DominioAccountResult,
)
from app.services.auth_service import get_api_key
from app.services.password_service import generate_password_dominio
from app.core.exceptions import create_error_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/execute-action",
    response_model=DominioActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar acción de Dominio",
    description="Ejecuta una acción simulada del dominio corporativo (buscar usuario, cambiar contraseña, desbloquear cuenta)",
    responses={
        200: {"description": "Acción ejecutada exitosamente"},
        400: {"description": "Request inválido (action_type no reconocido, user_name faltante para find_user)"},
        401: {"description": "API Key inválida o faltante"},
        422: {"description": "Validación de datos fallida"},
        500: {"description": "Error interno del servidor"},
    },
)
async def execute_action(
    request: DominioActionRequest,
    api_key: str = Depends(get_api_key),
) -> DominioActionResponse:
    """
    Ejecuta una acción del dominio corporativo.
    
    Acciones soportadas:
    - find_user: Consulta usuario por nombre de funcionario
    - change_password: Cambia contraseña (mínimo 10 caracteres, mayúsculas, minúsculas, números, símbolos opcionales)
    - unlock_account: Desbloquea cuenta de usuario
    """
    try:
        # Validar action_type
        valid_actions = ["find_user", "change_password", "unlock_account"]
        if request.action_type not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    error_code="invalid_action_type",
                    message="El tipo de acción solicitada no es válido.",
                    detail=f"Tipo de acción '{request.action_type}' no válido",
                    action_suggestion="Verifica que la acción sea una de las permitidas: buscar usuario, cambiar contraseña o desbloquear cuenta.",
                ),
            )

        # Validar user_name para find_user
        if request.action_type == "find_user" and not request.user_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    error_code="missing_user_name",
                    message="El nombre de usuario es requerido para buscar un usuario.",
                    detail="user_name es requerido para la acción find_user",
                    action_suggestion="Proporciona el nombre de usuario en el campo 'user_name'.",
                ),
            )

        # Simular procesamiento (sleep 2 segundos)
        await asyncio.sleep(2)

        if request.action_type == "find_user":
            # Simular búsqueda de usuario (búsqueda parcial, case-insensitive)
            user_name = request.user_name.lower()
            
            # Simulación: si el nombre contiene "test" o "demo", no se encuentra
            # De lo contrario, se encuentra
            found = "test" not in user_name and "demo" not in user_name
            
            if found:
                result = DominioFindUserResult(
                    user_id=f"simulated_user_{request.user_id}",
                    user_name=request.user_name,
                    email=f"{request.user_name}@aguasdemanizales.com.co",
                    status="active",
                    found=True,
                )
                message = f"Usuario '{request.user_name}' encontrado exitosamente"
            else:
                result = DominioFindUserResult(
                    user_id=None,
                    user_name=request.user_name,
                    email=None,
                    status=None,
                    found=False,
                )
                message = f"Usuario '{request.user_name}' no encontrado"
            
            return DominioActionResponse(
                success=True,
                action_type=request.action_type,
                result=result.model_dump(),
                message=message,
                generated_password=None,
            )

        elif request.action_type == "change_password":
            # Generar contraseña
            try:
                password = generate_password_dominio()
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
            
            result = DominioPasswordResult(
                password_length=len(password),
                changed_at=timestamp,
            )
            
            return DominioActionResponse(
                success=True,
                action_type=request.action_type,
                result=result.model_dump(),
                message="Contraseña cambiada exitosamente",
                generated_password=password,
            )

        elif request.action_type == "unlock_account":
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            result = DominioAccountResult(
                account_status="unlocked",
                action_timestamp=timestamp,
            )
            
            return DominioActionResponse(
                success=True,
                action_type=request.action_type,
                result=result.model_dump(),
                message="Cuenta desbloqueada exitosamente",
                generated_password=None,
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

