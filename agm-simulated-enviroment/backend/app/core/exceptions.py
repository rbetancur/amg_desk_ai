"""
Excepciones personalizadas para el backend.
"""
from datetime import datetime


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
    detail: str | None = None,
) -> dict:
    """
    Crea una respuesta de error estandarizada.
    
    Args:
        error_code: Código del error
        message: Mensaje legible para el usuario
        detail: Detalle técnico opcional
        
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
    
    return response

