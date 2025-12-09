"""
Router para endpoints de acción del dominio corporativo.
Simula las acciones que el Agente AI ejecutará.
"""
import asyncio
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

router = APIRouter()


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
    # Validar action_type
    valid_actions = ["find_user", "change_password", "unlock_account"]
    if request.action_type not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de acción '{request.action_type}' no válido. Acciones permitidas: {', '.join(valid_actions)}",
        )

    # Validar user_name para find_user
    if request.action_type == "find_user" and not request.user_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_name es requerido para la acción find_user",
        )

    # Simular procesamiento (sleep 2 segundos)
    await asyncio.sleep(2)

    try:
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
            password = generate_password_dominio()
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar acción: {str(e)}",
        )

