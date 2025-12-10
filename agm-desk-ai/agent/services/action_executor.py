"""Ejecutor de acciones para comunicarse con el backend FastAPI"""
import asyncio
import structlog
from typing import Optional, Literal, Callable, Any
import httpx
from agent.core.config import Settings
from agent.core.exceptions import (
    ActionExecutionError,
    BackendConnectionError,
    InvalidActionError,
    AuthenticationError
)

logger = structlog.get_logger(__name__)


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Reintenta una función async con backoff exponencial.
    
    Args:
        func: Función async a ejecutar
        max_retries: Número máximo de reintentos
        initial_delay: Delay inicial en segundos
        *args, **kwargs: Argumentos para la función
    
    Returns:
        Resultado de la función
    
    Raises:
        Última excepción si todos los reintentos fallan
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException, httpx.ConnectError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    "Reintentando después de error",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay=delay,
                    error_type=type(e).__name__
                )
                await asyncio.sleep(delay)
                delay *= 2  # Backoff exponencial
            else:
                raise
    raise last_exception


def extract_backend_error_message(error_response: dict) -> tuple[str, Optional[str], Optional[str]]:
    """
    Extrae mensaje amigable, acción sugerida y detalle técnico de respuesta de error del backend.
    
    Args:
        error_response: Respuesta de error del backend (dict)
    
    Returns:
        Tupla (user_message, action_suggestion, technical_detail)
    """
    # Intentar extraer de estructura estándar del backend
    message = error_response.get("message", "Ocurrió un error al procesar la solicitud.")
    action_suggestion = error_response.get("action_suggestion")
    technical_detail = error_response.get("detail")  # Solo para logs
    
    return message, action_suggestion, technical_detail


def get_http_status_fallback_message(status_code: int) -> tuple[str, str]:
    """
    Retorna mensaje amigable y acción sugerida según código HTTP (fallback).
    
    Args:
        status_code: Código HTTP de error
    
    Returns:
        Tupla (user_message, action_suggestion)
    """
    fallback_messages = {
        400: (
            "No se pudo procesar la solicitud. Por favor, verifica que todos los datos sean correctos.",
            "Revisa los datos enviados y vuelve a intentar."
        ),
        401: (
            "Error de autenticación con el sistema. El agente se reconectará automáticamente.",
            "Tu solicitud será procesada cuando el sistema se reconecte. No es necesario hacer nada."
        ),
        403: (
            "No se tienen permisos para ejecutar esta acción en el sistema.",
            "Contacta al administrador del sistema si crees que esto es un error."
        ),
        404: (
            "El recurso solicitado no existe en el sistema.",
            "Tu solicitud será reintentada automáticamente."
        ),
        422: (
            "Los datos enviados no son válidos. Por favor, verifica la información.",
            "Tu solicitud será procesada con los datos disponibles."
        ),
        500: (
            "El sistema temporalmente no está disponible. Tu solicitud será procesada automáticamente cuando el servicio se recupere.",
            "No es necesario hacer nada. El sistema reintentará automáticamente."
        ),
        503: (
            "El servicio está temporalmente no disponible. Tu solicitud será reintentada automáticamente.",
            "No es necesario hacer nada. El sistema reintentará automáticamente."
        ),
    }
    
    return fallback_messages.get(
        status_code,
        (
            "Ocurrió un error al procesar la solicitud.",
            "Tu solicitud será reintentada automáticamente."
        )
    )


def sanitize_password_for_logging(password: Optional[str]) -> str:
    """Sanitiza contraseña para logging (no loggear contraseñas reales)"""
    if password:
        return "[REDACTED]"
    return "None"


class ActionExecutor:
    """Ejecutor de acciones para comunicarse con el backend FastAPI"""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el ejecutor de acciones.
        
        Args:
            settings: Configuración del agente
        """
        self.settings = settings
        self.base_url = settings.BACKEND_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            "ActionExecutor inicializado",
            backend_url=self.base_url,
            timeout=30.0
        )
    
    def _get_headers(self) -> dict:
        """Retorna headers necesarios para las solicitudes HTTP"""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.settings.API_SECRET_KEY
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict] = None
    ) -> dict:
        """
        Realiza una solicitud HTTP al backend.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo (ej: /api/apps/amerika/execute-action)
            payload: Payload JSON opcional
        
        Returns:
            Respuesta parseada como dict
        
        Raises:
            BackendConnectionError: Error de conexión
            ActionExecutionError: Error en la ejecución
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()  # Lanza HTTPStatusError si status >= 400
            return response.json()
        except httpx.ConnectError as e:
            logger.error("Error de conexión con backend", endpoint=endpoint, error=str(e))
            raise BackendConnectionError(
                user_message="No se pudo conectar con el sistema. El servicio puede estar temporalmente no disponible.",
                action_suggestion="Tu solicitud será reintentada automáticamente cuando el servicio se recupere.",
                technical_detail=str(e)
            )
        except httpx.TimeoutException as e:
            logger.error("Timeout en solicitud al backend", endpoint=endpoint, timeout=30.0)
            raise BackendConnectionError(
                user_message="La solicitud tardó demasiado en procesarse.",
                action_suggestion="Tu solicitud será reintentada automáticamente.",
                technical_detail=f"Timeout después de 30 segundos: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            # Manejar en métodos específicos con extract_backend_error_message()
            raise
        except httpx.RequestError as e:
            logger.error("Error genérico en solicitud", endpoint=endpoint, error=str(e))
            raise BackendConnectionError(
                user_message="Ocurrió un error al comunicarse con el sistema.",
                action_suggestion="Tu solicitud será reintentada automáticamente.",
                technical_detail=str(e)
            )
        except ValueError as e:
            logger.error("Error al parsear respuesta JSON", endpoint=endpoint, error=str(e))
            raise ActionExecutionError(
                user_message="El sistema retornó una respuesta inválida.",
                action_suggestion="Tu solicitud será reintentada automáticamente.",
                technical_detail=str(e)
            )
        except Exception as e:
            logger.error("Error inesperado en solicitud", endpoint=endpoint, error=str(e), exc_info=True)
            raise ActionExecutionError(
                user_message="Ocurrió un error inesperado al procesar tu solicitud.",
                action_suggestion="Tu solicitud será reintentada automáticamente.",
                technical_detail=str(e)
            )
    
    async def execute_amerika_action(
        self,
        user_id: str,
        action_type: Literal["generate_password", "unlock_account", "lock_account"]
    ) -> dict:
        """
        Ejecuta una acción de Amerika.
        
        Args:
            user_id: ID del usuario
            action_type: Tipo de acción a ejecutar
        
        Returns:
            Respuesta parseada según esquema AmerikaActionResponse
        
        Raises:
            ActionExecutionError: Si la acción falla
            InvalidActionError: Si la acción no es válida
            AuthenticationError: Si hay error de autenticación
        """
        endpoint = "/api/apps/amerika/execute-action"
        payload = {
            "user_id": user_id,
            "action_type": action_type
        }
        
        print(f"🔌 Invocando API: {endpoint} | Acción: {action_type} | Usuario: {user_id}")
        logger.info(
            "Ejecutando acción de Amerika",
            user_id=user_id,
            action_type=action_type,
            endpoint=endpoint
        )
        
        async def _execute():
            return await self._make_request("POST", endpoint, payload)
        
        try:
            response = await retry_with_backoff(
                _execute,
                max_retries=self.settings.MAX_RETRIES,
                initial_delay=self.settings.RETRY_DELAY
            )
            
            # Sanitizar contraseña para logging
            sanitized_password = sanitize_password_for_logging(response.get("generated_password"))
            logger.info(
                "Acción de Amerika ejecutada exitosamente",
                user_id=user_id,
                action_type=action_type,
                success=response.get("success"),
                generated_password=sanitized_password
            )
            
            return response
            
        except httpx.HTTPStatusError as e:
            # Intentar extraer mensaje amigable del backend
            try:
                error_data = e.response.json() if e.response else {}
            except (ValueError, AttributeError):
                error_data = {}
            
            user_message, action_suggestion, technical_detail = extract_backend_error_message(error_data)
            
            # Si no hay mensaje del backend, usar fallback según código HTTP
            if not user_message or user_message == "Ocurrió un error al procesar la solicitud.":
                user_message, action_suggestion = get_http_status_fallback_message(e.response.status_code if e.response else 500)
            
            # Registrar detalle técnico en logs (NO mostrar al usuario)
            logger.error(
                "Error al ejecutar acción de Amerika",
                user_id=user_id,
                action_type=action_type,
                status_code=e.response.status_code if e.response else None,
                technical_detail=technical_detail
            )
            
            # Lanzar excepción apropiada según código HTTP
            if e.response and e.response.status_code == 401:
                raise AuthenticationError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code,
                    technical_detail=technical_detail
                )
            elif e.response and e.response.status_code == 400:
                raise InvalidActionError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code,
                    technical_detail=technical_detail
                )
            else:
                raise ActionExecutionError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code if e.response else None,
                    technical_detail=technical_detail
                )
    
    async def execute_dominio_action(
        self,
        user_id: str,
        action_type: Literal["find_user", "change_password", "unlock_account"],
        user_name: Optional[str] = None
    ) -> dict:
        """
        Ejecuta una acción de Dominio.
        
        Args:
            user_id: ID del usuario
            action_type: Tipo de acción a ejecutar
            user_name: Nombre de usuario (requerido para find_user)
        
        Returns:
            Respuesta parseada según esquema DominioActionResponse
        
        Raises:
            ActionExecutionError: Si la acción falla
            InvalidActionError: Si la acción no es válida o user_name faltante
            AuthenticationError: Si hay error de autenticación
        """
        # Validar que user_name esté presente cuando action_type == "find_user"
        if action_type == "find_user" and not user_name:
            raise InvalidActionError(
                user_message="El nombre de usuario es requerido para buscar un usuario.",
                action_suggestion="Proporciona el nombre de usuario en el campo 'user_name'.",
                technical_detail="user_name es requerido para la acción find_user"
            )
        
        endpoint = "/api/apps/dominio/execute-action"
        payload = {
            "user_id": user_id,
            "action_type": action_type
        }
        if user_name:
            payload["user_name"] = user_name
        
        user_name_display = user_name if user_name else "N/A"
        print(f"🔌 Invocando API: {endpoint} | Acción: {action_type} | Usuario: {user_id} | Nombre: {user_name_display}")
        logger.info(
            "Ejecutando acción de Dominio",
            user_id=user_id,
            action_type=action_type,
            user_name=user_name,
            endpoint=endpoint
        )
        
        async def _execute():
            return await self._make_request("POST", endpoint, payload)
        
        try:
            response = await retry_with_backoff(
                _execute,
                max_retries=self.settings.MAX_RETRIES,
                initial_delay=self.settings.RETRY_DELAY
            )
            
            # Sanitizar contraseña para logging
            sanitized_password = sanitize_password_for_logging(response.get("generated_password"))
            logger.info(
                "Acción de Dominio ejecutada exitosamente",
                user_id=user_id,
                action_type=action_type,
                success=response.get("success"),
                found=response.get("result", {}).get("found") if action_type == "find_user" else None,
                generated_password=sanitized_password
            )
            
            return response
            
        except httpx.HTTPStatusError as e:
            # Intentar extraer mensaje amigable del backend
            try:
                error_data = e.response.json() if e.response else {}
            except (ValueError, AttributeError):
                error_data = {}
            
            user_message, action_suggestion, technical_detail = extract_backend_error_message(error_data)
            
            # Si no hay mensaje del backend, usar fallback según código HTTP
            if not user_message or user_message == "Ocurrió un error al procesar la solicitud.":
                user_message, action_suggestion = get_http_status_fallback_message(e.response.status_code if e.response else 500)
            
            # Registrar detalle técnico en logs (NO mostrar al usuario)
            logger.error(
                "Error al ejecutar acción de Dominio",
                user_id=user_id,
                action_type=action_type,
                user_name=user_name,
                status_code=e.response.status_code if e.response else None,
                technical_detail=technical_detail
            )
            
            # Lanzar excepción apropiada según código HTTP
            if e.response and e.response.status_code == 401:
                raise AuthenticationError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code,
                    technical_detail=technical_detail
                )
            elif e.response and e.response.status_code == 400:
                raise InvalidActionError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code,
                    technical_detail=technical_detail
                )
            else:
                raise ActionExecutionError(
                    user_message=user_message,
                    action_suggestion=action_suggestion,
                    status_code=e.response.status_code if e.response else None,
                    technical_detail=technical_detail
                )
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
        logger.info("ActionExecutor cerrado")

