"""
Excepciones personalizadas para el backend.
"""
from datetime import datetime
from typing import Optional


class RequestNotFoundError(Exception):
    """Excepción cuando una solicitud no se encuentra"""
    pass


class UnauthorizedError(Exception):
    """Excepción cuando el usuario no está autenticado"""
    pass


class ForbiddenError(Exception):
    """Excepción cuando el usuario no tiene permisos"""
    pass


class ValidationError(Exception):
    """Excepción cuando hay un error de validación"""
    pass


def create_error_response(
    error_code: str,
    message: str,
    detail: Optional[str] = None,
    action_suggestion: Optional[str] = None,
) -> dict:
    """
    Crea una respuesta de error estandarizada.
    
    Args:
        error_code: Código del error
        message: Mensaje legible para el usuario
        detail: Detalle técnico opcional (solo para logs, no se muestra al usuario)
        action_suggestion: Sugerencia de acción para el usuario (opcional)
        
    Returns:
        dict: Respuesta de error con estructura estándar
    """
    response = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if detail:
        response["detail"] = detail
    
    if action_suggestion:
        response["action_suggestion"] = action_suggestion
    
    return response

