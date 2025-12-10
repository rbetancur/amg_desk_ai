"""Excepciones personalizadas para el Agente AI"""
from typing import Optional


class AgentError(Exception):
    """Excepción base para errores del agente"""
    pass


class ConfigurationError(AgentError):
    """Error de configuración"""
    pass


class SupabaseConnectionError(AgentError):
    """Error de conexión con Supabase"""
    pass


class BackendConnectionError(AgentError):
    """Error de conexión con backend"""
    def __init__(
        self,
        user_message: str,
        action_suggestion: Optional[str] = None,
        technical_detail: Optional[str] = None
    ):
        self.user_message = user_message
        self.action_suggestion = action_suggestion
        self.technical_detail = technical_detail
        super().__init__(user_message)


class AIClassificationError(AgentError):
    """Error en clasificación de IA"""
    pass


class ActionExecutionError(AgentError):
    """Excepción cuando falla la ejecución de una acción en el backend"""
    def __init__(
        self,
        user_message: str,
        action_suggestion: Optional[str] = None,
        status_code: Optional[int] = None,
        technical_detail: Optional[str] = None
    ):
        self.user_message = user_message
        self.action_suggestion = action_suggestion
        self.status_code = status_code
        self.technical_detail = technical_detail
        super().__init__(user_message)


class InvalidActionError(ActionExecutionError):
    """Acción no válida o parámetros incorrectos"""
    pass


class AuthenticationError(ActionExecutionError):
    """Error de autenticación con backend"""
    pass


class ValidationError(AgentError):
    """Error de validación de solicitud"""
    pass


class RateLimitExceededError(ValidationError):
    """Error cuando se excede el límite de solicitudes"""
    def __init__(
        self,
        user_message: str,
        current_count: int,
        limit: int,
        window_hours: int,
        action_suggestion: Optional[str] = None
    ):
        self.user_message = user_message
        self.current_count = current_count
        self.limit = limit
        self.window_hours = window_hours
        self.action_suggestion = action_suggestion
        super().__init__(user_message)

