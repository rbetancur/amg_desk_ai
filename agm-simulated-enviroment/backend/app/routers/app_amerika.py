"""
Router para endpoints de acción de la aplicación Amerika.
Simula las acciones que el Agente AI ejecutará.
"""
import asyncio
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

router = APIRouter()


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
    # Validar action_type
    valid_actions = ["generate_password", "unlock_account", "lock_account"]
    if request.action_type not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de acción '{request.action_type}' no válido. Acciones permitidas: {', '.join(valid_actions)}",
        )

    # Simular procesamiento (sleep 2 segundos)
    await asyncio.sleep(2)

    try:
        if request.action_type == "generate_password":
            # Generar contraseña
            password = generate_password_amerika()
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar acción: {str(e)}",
        )

