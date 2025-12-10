# Especificación Detallada: Agente AI (Orquestador)

Este documento detalla la implementación del Agente AI (Orquestador) que procesa solicitudes en tiempo real, expandiendo el "Siguiente Paso" del plan de desarrollo principal con especificaciones técnicas completas.

## Descripción

Desarrollar el Agente AI (Orquestador) que escucha eventos Realtime de Supabase, procesa solicitudes con Gemini AI, ejecuta acciones en el backend FastAPI y actualiza las solicitudes en la base de datos.

**Contexto**: Este agente es un servicio consumidor independiente que automatiza el flujo completo de atención de mesas de servicio. Escucha nuevas solicitudes en tiempo real, las clasifica con IA, ejecuta las acciones técnicas necesarias y actualiza el estado de las solicitudes.

**Referencias**:
- [Plan de Desarrollo Principal](./02_dev_plan.md#siguiente-paso)
- [Estructura del Agente AI](../docs/README.md#estructura-del-agente-ai-agm-desk-ai)
- [Especificación del Backend](./03_backend_detailed.md)
- [Flujo Actual](../docs/flujo%20actual.md)

---

## Capacidades de IA Requeridas

El Agente AI utiliza **Gemini 2.5 Flash** para las siguientes capacidades de procesamiento de lenguaje natural (NLP):

### 1. Clasificación de Texto
**Capacidad**: Determinar si la solicitud pertenece a la categoría "Amerika" o "Dominio" basándose en la descripción proporcionada por el usuario.

**Implementación**: 
- Se utiliza un System Prompt especializado para clasificación
- La respuesta se estructura en formato JSON con `app_type`, `confidence`, `detected_actions` y `reasoning`
- Ver FASE 3.4 (Clasificación de Solicitudes con Respuesta JSON Estructurada) para detalles completos

### 2. Extracción de Entidades (NLP)
**Capacidad**: Extraer información clave de la descripción de la solicitud, como:
- Nombre de usuario (cuando se menciona explícitamente)
- Tipo de acción específica requerida (cambio de contraseña o desbloqueo)
- Parámetros adicionales necesarios para ejecutar las acciones

**Implementación**:
- La extracción se realiza durante la clasificación (una sola llamada a Gemini)
- Los parámetros extraídos se incluyen en `extracted_params` del resultado de clasificación
- Ver FASE 3.7 (Extracción de Parámetros) para detalles completos

### 3. Generación de Respuestas Estructuradas
**Capacidad**: Producir respuestas en formato JSON válido para procesamiento automatizado.

**Implementación**:
- Se utiliza `response_mime_type="application/json"` para garantizar respuestas JSON válidas
- La respuesta se valida con Pydantic `ClassificationResult` para garantizar estructura correcta
- Ver FASE 3.4 para detalles sobre validación y estructuración

### Nota Importante sobre Generación de Mensajes Finales

**La generación de mensajes finales al usuario (bitácora en `SOLUCION`) se realiza mediante lógica programática, no con IA adicional**:
- Los mensajes se generan usando plantillas predefinidas basadas en las acciones ejecutadas
- Esto reduce costos (no requiere llamadas adicionales a Gemini)
- Garantiza consistencia y formato profesional en la comunicación con el usuario
- Los mensajes son estructurados y predefinidos según el resultado de las acciones técnicas
- Ver FASE 5.4 (Actualización de Solicitudes en Supabase) para detalles sobre generación de mensajes

---

## FASE 1: Configuración del Proyecto y Setup

**Justificación**: Establecer la estructura base del proyecto con todas las herramientas y configuraciones necesarias antes de implementar funcionalidades específicas.

### 1.1. Configuración de Dependencias y Estructura

**Objetivo**: Configurar el proyecto Python con todas las dependencias necesarias y la estructura de carpetas.

**Tareas**:
1. Crear/actualizar `pyproject.toml` con dependencias:
   - `python >= 3.11`
   - `pydantic >= 2.0` (para configuración con pydantic-settings)
   - `pydantic-settings >= 2.0` (para gestión de variables de entorno)
   - `supabase >= 2.0` (SDK de Supabase para Python)
   - `httpx >= 0.25.0` (cliente HTTP asíncrono para llamadas al backend)
   - `google-generativeai >= 0.3.0` (SDK de Gemini AI)
   - `python-dotenv >= 1.0.0` (carga de variables de entorno desde .env)
   - `structlog >= 23.0.0` (logging estructurado)
   - `asyncio` (ya incluido en Python estándar)

2. Verificar estructura de carpetas:
   ```
   agm-desk-ai/
   ├── agent/
   │   ├── __init__.py
   │   ├── main.py                    # Punto de entrada
   │   ├── core/
   │   │   ├── __init__.py
   │   │   └── config.py             # Configuración centralizada
   │   ├── prompts/                   # Prompts reutilizables (nuevo)
   │   │   ├── __init__.py
   │   │   ├── system_prompts.py      # System prompts reutilizables
   │   │   └── templates/             # Templates de prompts (opcional)
   │   │       └── classification.json
   │   └── services/
   │       ├── __init__.py
   │       ├── realtime_listener.py  # Listener de Supabase Realtime
   │       ├── ai_processor.py       # Procesamiento con Gemini AI
   │       └── action_executor.py   # Ejecutor de acciones del backend
   ├── pyproject.toml
   ├── .env.example
   └── .gitignore
   ```

3. Crear `.env.example` con todas las variables de entorno necesarias (ver sección "Variables de Entorno")

4. Configurar `.gitignore` para excluir:
   - `.env`
   - `__pycache__/`
   - `*.pyc`
   - `.venv/`
   - `venv/`

**Archivos a crear/modificar**:
- `agm-desk-ai/pyproject.toml`
- `agm-desk-ai/.env.example`
- `agm-desk-ai/.gitignore`
- `agm-desk-ai/agent/prompts/` (nuevo directorio)
- `agm-desk-ai/agent/prompts/__init__.py` (nuevo)
- `agm-desk-ai/agent/prompts/system_prompts.py` (nuevo)

### 1.2. Configuración Centralizada (config.py)

**Objetivo**: Implementar gestión centralizada de configuración usando pydantic-settings.

**Tareas**:
1. Crear `agent/core/config.py` con clase `Settings` que herede de `BaseSettings` (pydantic-settings):
   - `SUPABASE_URL: str` - URL del proyecto Supabase
   - `SUPABASE_SERVICE_ROLE_KEY: str` - Service role key para bypass de RLS
   - `BACKEND_URL: str` - URL del backend FastAPI (default: `http://localhost:8000`)
   - `API_SECRET_KEY: str` - API Key para autenticación con backend
   - `GEMINI_API_KEY: str` - API Key de Gemini AI
   - `GEMINI_MODEL: str` - Modelo de Gemini a usar (default: `gemini-2.5-flash` para PoC, `gemini-1.5-pro` para producción)
   - `GEMINI_TEMPERATURE: float` - Temperatura para generación (default: `0.2`)
   - `GEMINI_MAX_TOKENS: int` - Máximo de tokens de salida (default: `500`)
   - `LOG_LEVEL: str` - Nivel de logging (default: `INFO`)
   - `MAX_RETRIES: int` - Número máximo de reintentos para acciones (default: 3)
   - `RETRY_DELAY: float` - Delay entre reintentos en segundos (default: 2.0)
   - `MAX_REQUESTS_PER_USER: int` - Número máximo de solicitudes por usuario en ventana de tiempo (default: 5)
   - `RATE_LIMIT_WINDOW_HOURS: int` - Ventana de tiempo en horas para rate limiting (default: 24)
   - `MIN_DESCRIPTION_LENGTH: int` - Longitud mínima de descripción (default: 10)
   - `MAX_DESCRIPTION_LENGTH: int` - Longitud máxima de descripción (default: 4000)
   - `PROMPT_INJECTION_KEYWORDS: str` - Palabras clave para detectar prompt injection (separadas por comas, default: "ignore,actúa,ejecuta,revela,bypass,override")
   - `DANGEROUS_INSTRUCTION_PATTERNS: str` - Patrones para detectar instrucciones peligrosas (separados por comas, default: "debes hacer,necesito que hagas,por favor ejecuta")
   - `MALICIOUS_CONTENT_KEYWORDS: str` - Palabras clave de contenido malicioso (separadas por comas, opcional)
   - `ENABLE_SECURITY_FILTERS: bool` - Habilitar filtros de seguridad (default: True)
   - `USE_FEW_SHOT_ALWAYS: bool` - Si True, siempre usa few-shot. Si False, usa few-shot solo cuando sea necesario (default: False)
   - `FEW_SHOT_THRESHOLD_DESCRIPTION_LENGTH: int` - Longitud mínima de descripción para considerar simple (sin few-shot) (default: 20)

2. Configurar carga de variables desde `.env`:
   - Usar `SettingsConfigDict` de pydantic-settings
   - Configurar `env_file = ".env"`
   - Configurar `case_sensitive = False`

3. Crear función helper `get_settings()` que retorne instancia singleton de `Settings`

4. Validar que todas las variables requeridas estén presentes al inicializar:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `BACKEND_URL`, `API_SECRET_KEY`, `GEMINI_API_KEY` son obligatorias
   - Lanzar excepción descriptiva si faltan variables críticas

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/core/config.py`

**Ejemplo de estructura**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    BACKEND_URL: str = "http://localhost:8000"
    API_SECRET_KEY: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Recomendado para PoC (más económico y rápido)
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_TOKENS: int = 500
    LOG_LEVEL: str = "INFO"
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    MAX_REQUESTS_PER_USER: int = 5
    RATE_LIMIT_WINDOW_HOURS: int = 24
    MIN_DESCRIPTION_LENGTH: int = 10
    MAX_DESCRIPTION_LENGTH: int = 4000
    PROMPT_INJECTION_KEYWORDS: str = "ignore,actúa,ejecuta,revela,bypass,override"
    DANGEROUS_INSTRUCTION_PATTERNS: str = "debes hacer,necesito que hagas,por favor ejecuta"
    MALICIOUS_CONTENT_KEYWORDS: str = ""
    ENABLE_SECURITY_FILTERS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

---

## FASE 2: Ejecutor de Acciones (action_executor.py)

**Justificación**: Implementar primero el ejecutor de acciones porque es independiente y permite probar la integración con el backend antes de implementar el procesamiento de IA.

### 2.1. Cliente HTTP para Backend

**Objetivo**: Crear cliente HTTP asíncrono para comunicarse con el backend FastAPI.

**Tareas**:
1. Crear clase `ActionExecutor` en `agent/services/action_executor.py`:
   - Inicializar con `settings: Settings`
   - Crear cliente `httpx.AsyncClient` con timeout configurable (default: 30 segundos)
   - Configurar base URL del backend desde `settings.BACKEND_URL`

2. Implementar método `_get_headers()` que retorne headers necesarios:
   - `Content-Type: application/json`
   - `X-API-Key: {settings.API_SECRET_KEY}` o `Authorization: Bearer {settings.API_SECRET_KEY}`

3. Implementar método helper `_make_request()` genérico:
   - Aceptar método HTTP, endpoint, payload (opcional)
   - Manejar errores HTTP (4xx, 5xx)
   - Retornar respuesta parseada como dict
   - Lanzar excepciones descriptivas para errores

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/action_executor.py`

### 2.2. Ejecución de Acciones de Amerika

**Objetivo**: Implementar métodos para ejecutar acciones de Amerika.

**Tareas**:
1. Implementar método `execute_amerika_action()`:
   - Parámetros: `user_id: str`, `action_type: Literal["generate_password", "unlock_account", "lock_account"]`
   - Construir payload según esquema `AmerikaActionRequest`:
     ```python
     {
         "user_id": user_id,
         "action_type": action_type
     }
     ```
   - Llamar a `POST {BACKEND_URL}/api/apps/amerika/execute-action`
   - Retornar respuesta parseada según esquema `AmerikaActionResponse`

2. Manejar errores específicos:
   - `400 Bad Request`: Acción no válida o parámetros incorrectos
   - `401 Unauthorized`: API Key inválida
   - `500 Internal Server Error`: Error en el backend
   - Retry automático con backoff exponencial (usar `MAX_RETRIES` y `RETRY_DELAY`)

3. Extraer información relevante de la respuesta:
   - `success`: Indica si la acción fue exitosa
   - `generated_password`: Contraseña generada (si aplica)
   - `message`: Mensaje descriptivo
   - `result`: Resultado completo de la acción

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/action_executor.py`

### 2.3. Ejecución de Acciones de Dominio

**Objetivo**: Implementar métodos para ejecutar acciones de Dominio.

**Tareas**:
1. Implementar método `execute_dominio_action()`:
   - Parámetros: `user_id: str`, `action_type: Literal["find_user", "change_password", "unlock_account"]`, `user_name: Optional[str] = None`
   - Construir payload según esquema `DominioActionRequest`:
     ```python
     {
         "user_id": user_id,
         "action_type": action_type,
         "user_name": user_name  # Solo para find_user
     }
     ```
   - Llamar a `POST {BACKEND_URL}/api/apps/dominio/execute-action`
   - Retornar respuesta parseada según esquema `DominioActionResponse`

2. Validar que `user_name` esté presente cuando `action_type == "find_user"`

3. Manejar errores específicos (similar a Amerika):
   - `400 Bad Request`: Acción no válida, `user_name` faltante para `find_user`
   - `401 Unauthorized`: API Key inválida
   - `500 Internal Server Error`: Error en el backend
   - Retry automático con backoff exponencial

4. Extraer información relevante de la respuesta:
   - `success`: Indica si la acción fue exitosa
   - `generated_password`: Contraseña generada (si aplica)
   - `message`: Mensaje descriptivo
   - `result`: Resultado completo de la acción (incluye `found` para `find_user`)

**Nota sobre `find_user`**: La acción `find_user` se ejecuta automáticamente SIEMPRE antes de `change_password` o `unlock_account` para Dominio. Esta acción valida que el usuario existe en el sistema antes de ejecutar acciones sobre su cuenta. Ver FASE 5.3, Paso 7.3 para la lógica completa de ejecución.

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/action_executor.py`

### 2.4. Manejo de Reintentos y Errores con Try-Catch Completo

**Objetivo**: Implementar lógica robusta de reintentos y manejo de errores con try-catch en todas las llamadas a APIs.

**Tareas**:
1. **Crear función helper `retry_with_backoff()`**:
   - Aceptar función async, número máximo de reintentos, delay inicial
   - Implementar backoff exponencial (delay se duplica en cada reintento)
   - Capturar excepciones específicas (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException, httpx.ConnectError)
   - Lanzar excepción después de agotar reintentos
   - Ejemplo de implementación:
     ```python
     async def retry_with_backoff(
         func: Callable,
         max_retries: int = 3,
         initial_delay: float = 2.0,
         *args,
         **kwargs
     ):
         delay = initial_delay
         last_exception = None
         
         for attempt in range(max_retries):
             try:
                 return await func(*args, **kwargs)
             except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException, httpx.ConnectError) as e:
                 last_exception = e
                 if attempt < max_retries - 1:
                     await asyncio.sleep(delay)
                     delay *= 2  # Backoff exponencial
                 else:
                     raise
         raise last_exception
     ```

2. **Aplicar try-catch en TODAS las llamadas HTTP**:
   - **En `_make_request()`**: Envolver `httpx.AsyncClient.request()` en try-catch
   - **Casos edge a manejar**:
     - `httpx.ConnectError`: Backend no disponible (conexión rechazada)
     - `httpx.TimeoutException`: Timeout en la solicitud
     - `httpx.HTTPStatusError`: Error HTTP (4xx, 5xx)
     - `httpx.RequestError`: Error genérico de solicitud
     - `ValueError`: Error al parsear JSON de respuesta
     - `KeyError`: Campo faltante en respuesta esperada
   - **Ejemplo de implementación**:
     ```python
     async def _make_request(self, method: str, endpoint: str, payload: Optional[dict] = None) -> dict:
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
                 action_suggestion="Tu solicitud será reintentada automáticamente cuando el servicio se recupere."
             )
         except httpx.TimeoutException as e:
             logger.error("Timeout en solicitud al backend", endpoint=endpoint, timeout=30.0)
             raise BackendConnectionError(
                 user_message="La solicitud tardó demasiado en procesarse.",
                 action_suggestion="Tu solicitud será reintentada automáticamente."
             )
         except httpx.HTTPStatusError as e:
             # Manejar en FASE 2.5 (Manejo de Errores HTTP del Backend con Mensajes Amigables)
             raise
         except httpx.RequestError as e:
             logger.error("Error genérico en solicitud", endpoint=endpoint, error=str(e))
             raise BackendConnectionError(
                 user_message="Ocurrió un error al comunicarse con el sistema.",
                 action_suggestion="Tu solicitud será reintentada automáticamente."
             )
         except ValueError as e:
             logger.error("Error al parsear respuesta JSON", endpoint=endpoint, error=str(e))
             raise ActionExecutionError(
                 user_message="El sistema retornó una respuesta inválida.",
                 action_suggestion="Tu solicitud será reintentada automáticamente."
             )
         except Exception as e:
             logger.error("Error inesperado en solicitud", endpoint=endpoint, error=str(e), exc_info=True)
             raise ActionExecutionError(
                 user_message="Ocurrió un error inesperado al procesar tu solicitud.",
                 action_suggestion="Tu solicitud será reintentada automáticamente."
             )
     ```

3. **Aplicar `retry_with_backoff()` a todos los métodos de ejecución de acciones**:
   - Envolver llamadas a `_make_request()` con `retry_with_backoff()`
   - Configurar `max_retries` desde `settings.MAX_RETRIES`
   - Configurar `initial_delay` desde `settings.RETRY_DELAY`

4. **Crear excepciones personalizadas** en `agent/core/exceptions.py`:
   - `ActionExecutionError`: Error genérico en ejecución de acción (con `user_message` y `action_suggestion`)
   - `BackendConnectionError`: Error de conexión con backend (hereda de `ActionExecutionError`)
   - `InvalidActionError`: Acción no válida o parámetros incorrectos
   - `AuthenticationError`: Error de autenticación con backend
   - Todas las excepciones deben incluir `user_message` y `action_suggestion` opcional

5. **Logging estructurado**:
   - Usar `structlog` para logging
   - Registrar intentos de ejecución, errores, reintentos
   - Incluir contexto relevante (user_id, action_type, endpoint, status_code, error_type)
   - **NO loggear contraseñas generadas** (usar `[REDACTED]` en logs)

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/action_executor.py`
- `agm-desk-ai/agent/core/exceptions.py` (nuevo)

### 2.5. Manejo de Errores HTTP del Backend con Mensajes Amigables (CRÍTICO - Requiere Backend Mejorado)

**Objetivo**: Traducir errores técnicos del backend a mensajes amigables para el usuario final, aprovechando las mejoras implementadas en el backend (FASE 4.1.1 de `03_backend_detailed.md`).

**Prerequisitos**: 
- ✅ El backend debe tener implementada la FASE 4.1.1 (Mensajes de Error Amigables)
- ✅ El backend debe retornar respuestas con estructura estándar: `{"error": "...", "message": "...", "action_suggestion": "...", "detail": "..."}`
- ✅ El frontend debe tener implementada la FASE 5.1.1 (Mejoras en Mensajes de Error Amigables)

**Justificación**: El backend ya retorna mensajes amigables en español con acciones sugeridas. El agente debe extraer estos mensajes y usarlos para actualizar las solicitudes con información clara para el usuario, evitando exponer detalles técnicos.

**Tareas**:
1. **Crear función `extract_backend_error_message()`** en `agent/services/action_executor.py`:
   - Extraer `message` y `action_suggestion` de respuestas de error del backend
   - Manejar diferentes formatos de error (FastAPI estándar, errores de conexión, etc.)
   - Retornar tupla `(user_message: str, action_suggestion: Optional[str], technical_detail: Optional[str])`
   ```python
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
   ```

2. **Mapeo de Códigos HTTP a Mensajes Amigables** (fallback si el backend no retorna estructura estándar):
   - **400 Bad Request**:
     - `user_message`: "No se pudo procesar la solicitud. Por favor, verifica que todos los datos sean correctos."
     - `action_suggestion`: "Revisa los datos enviados y vuelve a intentar."
   - **401 Unauthorized**:
     - `user_message`: "Error de autenticación con el sistema. El agente se reconectará automáticamente."
     - `action_suggestion`: "Tu solicitud será procesada cuando el sistema se reconecte. No es necesario hacer nada."
   - **403 Forbidden**:
     - `user_message`: "No se tienen permisos para ejecutar esta acción en el sistema."
     - `action_suggestion`: "Contacta al administrador del sistema si crees que esto es un error."
   - **404 Not Found**:
     - `user_message`: "El recurso solicitado no existe en el sistema."
     - `action_suggestion`: "Tu solicitud será reintentada automáticamente."
   - **422 Unprocessable Entity**:
     - `user_message`: "Los datos enviados no son válidos. Por favor, verifica la información."
     - `action_suggestion`: "Tu solicitud será procesada con los datos disponibles."
   - **500 Internal Server Error**:
     - `user_message`: "El sistema temporalmente no está disponible. Tu solicitud será procesada automáticamente cuando el servicio se recupere."
     - `action_suggestion`: "No es necesario hacer nada. El sistema reintentará automáticamente."
   - **503 Service Unavailable**:
     - `user_message`: "El servicio está temporalmente no disponible. Tu solicitud será reintentada automáticamente."
     - `action_suggestion`: "No es necesario hacer nada. El sistema reintentará automáticamente."

3. **Actualizar métodos de ejecución de acciones** (`execute_amerika_action()`, `execute_dominio_action()`):
   - Capturar errores HTTP del backend
   - Extraer mensaje amigable usando `extract_backend_error_message()`
   - Si el backend retorna estructura estándar, usar `message` y `action_suggestion` directamente
   - Si no, usar mapeo de códigos HTTP como fallback
   - **NO exponer detalles técnicos** en mensajes al usuario (usar solo para logs)
   - Ejemplo de implementación:
     ```python
     try:
         response = await self._make_request("POST", endpoint, payload)
         return response
     except httpx.HTTPStatusError as e:
         # Intentar extraer mensaje amigable del backend
         error_data = e.response.json() if e.response else {}
         user_message, action_suggestion, technical_detail = extract_backend_error_message(error_data)
         
         # Registrar detalle técnico en logs (NO mostrar al usuario)
         logger.error(
             "Error al ejecutar acción",
             user_id=user_id,
             action_type=action_type,
             status_code=e.response.status_code,
             technical_detail=technical_detail
         )
         
         # Lanzar excepción con mensaje amigable
         raise ActionExecutionError(
             user_message=user_message,
             action_suggestion=action_suggestion,
             status_code=e.response.status_code
         )
     ```

4. **Actualizar solicitud con mensaje amigable cuando falle ejecución de acción**:
   - Si una acción falla, actualizar `SOLUCION` con mensaje amigable del backend
   - Incluir `action_suggestion` si está disponible
   - Establecer `CODESTADO = 3` (SOLUCIONADO) pero con mensaje de error amigable
   - Agregar información en `AI_CLASSIFICATION_DATA`:
     ```python
     {
         "action_failed": True,
         "failure_reason": user_message,  # Mensaje amigable, NO técnico
         "action_suggestion": action_suggestion,
         "failure_timestamp": datetime.utcnow().isoformat(),
         "technical_detail": technical_detail  # Solo para auditoría, NO mostrar al usuario
     }
     ```

5. **Crear excepción `ActionExecutionError` mejorada**:
   ```python
   class ActionExecutionError(Exception):
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
   ```

6. **Validar que NO se expongan detalles técnicos**:
   - NO incluir stack traces en mensajes al usuario
   - NO incluir códigos de error técnicos en mensajes al usuario
   - NO incluir mensajes de excepción raw en mensajes al usuario
   - NO incluir URLs internas o detalles de configuración en mensajes al usuario
   - Usar `technical_detail` solo para logs estructurados

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/action_executor.py`
- `agm-desk-ai/agent/core/exceptions.py` (agregar `ActionExecutionError` mejorada)

**Nota Importante**: Esta sección **REQUIERE** que el backend tenga implementada la FASE 4.1.1 (Mensajes de Error Amigables) y el frontend tenga implementada la FASE 5.1.1 (Mejoras en Mensajes de Error Amigables). Verificar que estas mejoras estén completas antes de implementar esta sección del agente.

---

## FASE 3: Procesamiento con Gemini AI (ai_processor.py)

**Justificación**: Implementar el procesamiento de IA después del ejecutor de acciones para poder probar la clasificación independientemente. Esta fase incluye optimización de prompts, gestión de System Prompts reutilizables y estructuración de respuestas en JSON.

**Objetivos de Optimización**:
- **Reducir tokens**: System Prompts cargados una vez, no regenerados
- **Minimizar llamadas**: Una sola llamada a Gemini por solicitud
- **Control de tokens**: Límites configurables y monitoreo
- **Respuestas estructuradas**: JSON validado con Pydantic
- **Mantenibilidad**: Prompts en archivos separados, fáciles de modificar

### 3.1. Gestión de System Prompts Reutilizables

**Objetivo**: Crear sistema de gestión de prompts reutilizables que no se regeneren en cada solicitud, facilitando mantenimiento, consistencia y optimización de tokens.

**Tareas**:
1. Crear módulo `agent/prompts/system_prompts.py`:
   - Definir constantes con System Prompts reutilizables
   - Cada prompt debe ser una constante de tipo string
   - Organizar por funcionalidad (clasificación, extracción, etc.)

2. Definir System Prompts para Clasificación (BASE y CON FEW-SHOT):

   **2.1. System Prompt BASE (sin ejemplos) - ~400-500 tokens**:
   ```python
   CLASSIFICATION_SYSTEM_PROMPT_BASE = """
   Eres un asistente especializado en clasificar solicitudes de mesa de servicio para gestión de accesos corporativos.
   
   CONTEXTO DEL SISTEMA:
   
   Categorías de Solicitudes:
   - Categoría 300: "Cambio de Contraseña Cuenta Dominio" → corresponde a aplicación tipo "dominio"
   - Categoría 400: "Cambio de Contraseña Amerika" → corresponde a aplicación tipo "amerika"
   
   IMPORTANTE - DETECCIÓN DE NECESIDADES REALES:
   - El usuario puede seleccionar mal la categoría, pero TÚ debes determinar su necesidad REAL basándote en su descripción
   - Si el usuario menciona AMBAS aplicaciones (Amerika Y Dominio), debes detectarlo y marcar requires_secondary_app=true
   - La categoría seleccionada es solo una pista, pero la descripción del usuario es la fuente de verdad
   - Si hay discrepancia entre categoría y descripción, prioriza lo que el usuario menciona explícitamente
   
   REGLAS DE CLASIFICACIÓN:
   
   1. DETERMINAR NECESIDAD REAL:
      - Analiza la descripción del usuario, NO solo la categoría
      - Si el usuario menciona "Amerika" o "dominio" explícitamente, esa es su necesidad real
      - Si menciona AMBAS, marca requires_secondary_app=true
   
   2. PRIORIZACIÓN:
      - Si el usuario menciona una aplicación explícitamente → esa es app_type (aunque la categoría sea diferente)
        * El sistema corregirá automáticamente la categoría al valor correcto
        * app_type="dominio" → CODCATEGORIA se actualizará a 300
        * app_type="amerika" → CODCATEGORIA se actualizará a 400
      - Si el usuario menciona ambas aplicaciones → app_type = la de la categoría, requires_secondary_app=true
      - Si no menciona ninguna explícitamente → usar categoría como guía, confidence más bajo (no corregir categoría)
   
   3. CONFIDENCE:
      - 0.9-1.0: Menciones explícitas de aplicación y acción, categoría coincide
      - 0.7-0.89: Menciones explícitas pero categoría diferente (confianza en descripción)
      - 0.5-0.69: Contexto claro pero sin mención explícita de aplicación
      - <0.5: Contexto insuficiente (usar fallback basado en categoría)
   
   4. DETECCIÓN DE MÚLTIPLES APLICACIONES:
      - Palabras clave que indican ambas: "tanto...como", "y también", "además de", "ambas", "las dos"
      - Si detectas ambas aplicaciones:
        * app_type = aplicación de la categoría (o la primera mencionada)
        * requires_secondary_app = true
        * secondary_app_actions = acciones detectadas para la otra aplicación
   
   Formato de respuesta requerido (JSON estricto):
   {
     "app_type": "amerika" | "dominio",
     "confidence": 0.0-1.0,
     "detected_actions": ["change_password", "unlock_account"],
     "reasoning": "Breve explicación (incluir si detectaste ambas aplicaciones o discrepancia con categoría)",
     "extracted_params": {
       "user_name": "nombre_usuario"  // Solo para dominio si se menciona explícitamente
     },
     "requires_secondary_app": false | true,
     "secondary_app_actions": null | ["change_password", "unlock_account"]
   }
   """
   ```

   **2.2. System Prompt CON FEW-SHOT (con ejemplos) - ~800-1000 tokens**:
   ```python
   CLASSIFICATION_SYSTEM_PROMPT_WITH_EXAMPLES = """
   Eres un asistente especializado en clasificar solicitudes de mesa de servicio para gestión de accesos corporativos.
   
   CONTEXTO DEL SISTEMA:
   
   Categorías de Solicitudes:
   - Categoría 300: "Cambio de Contraseña Cuenta Dominio" → corresponde a aplicación tipo "dominio"
   - Categoría 400: "Cambio de Contraseña Amerika" → corresponde a aplicación tipo "amerika"
   
   IMPORTANTE - DETECCIÓN DE NECESIDADES REALES:
   - El usuario puede seleccionar mal la categoría, pero TÚ debes determinar su necesidad REAL basándote en su descripción
   - Si el usuario menciona AMBAS aplicaciones (Amerika Y Dominio), debes detectarlo y marcar requires_secondary_app=true
   - La categoría seleccionada es solo una pista, pero la descripción del usuario es la fuente de verdad
   - Si hay discrepancia entre categoría y descripción, prioriza lo que el usuario menciona explícitamente
   
   EJEMPLOS DE CLASIFICACIÓN (Few-Shot):
   
   Ejemplo 1 - Una sola aplicación, categoría correcta:
   Input: {"codcategoria": 400, "description": "Necesito cambiar mi contraseña de Amerika"}
   Output: {
     "app_type": "amerika",
     "confidence": 0.95,
     "detected_actions": ["change_password"],
     "reasoning": "Menciona explícitamente Amerika y cambio de contraseña. Categoría coincide.",
     "extracted_params": {},
     "requires_secondary_app": false,
     "secondary_app_actions": null
   }
   
   Ejemplo 2 - AMBAS aplicaciones mencionadas explícitamente:
   Input: {"codcategoria": 300, "description": "Necesito cambiar contraseña de dominio y desbloquear mi cuenta de Amerika"}
   Output: {
     "app_type": "dominio",
     "confidence": 0.92,
     "detected_actions": ["change_password"],
     "reasoning": "Usuario menciona explícitamente ambas aplicaciones: dominio (cambio contraseña) y Amerika (desbloqueo). Se procesarán ambas.",
     "extracted_params": {},
     "requires_secondary_app": true,
     "secondary_app_actions": ["unlock_account"]
   }
   
   Ejemplo 3 - Categoría incorrecta, usuario menciona la correcta:
   Input: {"codcategoria": 300, "description": "Necesito cambiar mi contraseña de Amerika porque la olvidé"}
   Output: {
     "app_type": "amerika",
     "confidence": 0.85,
     "detected_actions": ["change_password"],
     "reasoning": "Usuario menciona explícitamente 'Amerika' pero seleccionó categoría 300 (dominio). Se detecta necesidad real: Amerika. El sistema corregirá automáticamente la categoría de 300 a 400.",
     "extracted_params": {},
     "requires_secondary_app": false,
     "secondary_app_actions": null
   }
   Nota: En este caso, el sistema debe:
   1. Detectar discrepancia: codcategoria=300 pero app_type="amerika"
   2. Calcular corrected_codcategoria=400 (según app_type detectado)
   3. Actualizar CODCATEGORIA de 300 a 400 en Supabase (corrección automática)
   4. Ejecutar la acción en Amerika (app_type detectado)
   5. Registrar en AI_CLASSIFICATION_DATA:
      - original_codcategoria: 300 (para auditoría)
      - corrected_codcategoria: 400
      - category_corrected: true
   
   Ejemplo 4 - Ambas aplicaciones, misma acción:
   Input: {"codcategoria": 400, "description": "Necesito cambiar contraseña tanto de Amerika como de dominio"}
   Output: {
     "app_type": "amerika",
     "confidence": 0.90,
     "detected_actions": ["change_password"],
     "reasoning": "Usuario requiere cambio de contraseña en ambas aplicaciones. Se procesarán ambas secuencialmente.",
     "extracted_params": {},
     "requires_secondary_app": true,
     "secondary_app_actions": ["change_password"]
   }
   
   REGLAS DE CLASIFICACIÓN:
   
   [Mismas reglas que CLASSIFICATION_SYSTEM_PROMPT_BASE]
   
   Formato de respuesta requerido (JSON estricto):
   {
     "app_type": "amerika" | "dominio",
     "confidence": 0.0-1.0,
     "detected_actions": ["change_password", "unlock_account"],
     "reasoning": "Breve explicación (incluir si detectaste ambas aplicaciones o discrepancia con categoría)",
     "extracted_params": {
       "user_name": "nombre_usuario"  // Solo para dominio si se menciona explícitamente
     },
     "requires_secondary_app": false | true,
     "secondary_app_actions": null | ["change_password", "unlock_account"]
   }
   """
   ```

   **Nota sobre Optimización de Tokens**:
   - El System Prompt BASE se usa para solicitudes simples (mayoría de casos) → ~400-500 tokens
   - El System Prompt CON FEW-SHOT se usa solo cuando se detecta complejidad → ~800-1000 tokens
   - La selección se hace automáticamente basándose en criterios de complejidad (ver FASE 3.3)
   - **Ahorro estimado**: ~40-50% de tokens en casos típicos (80% simples, 20% complejos)

3. Definir estructura de respuesta JSON (`CLASSIFICATION_RESPONSE_SCHEMA`):
   - Crear clase Pydantic o dict con estructura esperada
   - Validar que Gemini retorne exactamente este formato
   - Incluir validación de tipos y valores permitidos

4. Implementar función `get_system_prompt(prompt_type: str) -> str`:
   - Parámetros: `prompt_type` (ej: "classification_base", "classification_with_examples")
   - Tipos disponibles:
     - `"classification_base"`: Prompt base sin ejemplos (~400-500 tokens)
     - `"classification_with_examples"`: Prompt con few-shot examples (~800-1000 tokens)
   - Retornar System Prompt correspondiente desde constantes
   - Cachear prompts en memoria para evitar re-lectura
   - Lanzar excepción si el tipo de prompt no existe

5. Crear función helper `load_prompts()`:
   - Cargar todos los System Prompts al inicializar el módulo
   - Validar que todos los prompts requeridos estén definidos
   - Retornar dict con todos los prompts disponibles

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/prompts/__init__.py` (nuevo)
- `agm-desk-ai/agent/prompts/system_prompts.py` (nuevo)

**Referencias para mantener consistencia**:
- **Mapeo de nomenclatura**: Ver [docs/NAMING_MAPPING.md](../docs/NAMING_MAPPING.md) para el mapeo completo de categorías, estados y convenciones
- **Categorías**: El System Prompt debe reflejar el mapeo de categorías definido en NAMING_MAPPING.md (300→dominio, 400→amerika)
- **Estados**: Los estados (1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO) están documentados en NAMING_MAPPING.md para referencia

**Ventajas de este enfoque**:
- **Optimización de tokens**: System Prompt se carga una vez, no se regenera
- **Mantenibilidad**: Fácil modificar prompts sin tocar código
- **Consistencia**: Mismo prompt para todas las solicitudes
- **Seguridad**: System Prompt incluye instrucciones de seguridad
- **Testabilidad**: Fácil testear con diferentes prompts
- **Contexto completo**: Incluye mapeo de categorías y estados para mejor clasificación

### 3.2. Configuración de Gemini AI con Optimización

**Objetivo**: Configurar cliente de Gemini AI con optimizaciones para reducir tokens y llamadas innecesarias.

**Tareas**:
1. Crear clase `AIProcessor` en `agent/services/ai_processor.py`:
   - Inicializar con `settings: Settings`
   - Configurar cliente de Gemini usando `google.generativeai.configure(api_key=settings.GEMINI_API_KEY)`
   - Seleccionar modelo: `gemini-2.5-flash` (recomendado para PoC - más económico y rápido) o `gemini-1.5-pro` (para producción - mayor precisión)
   - Configurar parámetros de generación:
     - `temperature`: 0.1-0.3 (bajo para respuestas consistentes y estructuradas)
     - `max_output_tokens`: 500 (suficiente para JSON de clasificación)
     - `top_p`: 0.8 (balance entre creatividad y consistencia)

2. Cargar System Prompts al inicializar:
   - Importar `get_system_prompt` desde `agent.prompts.system_prompts`
   - Cargar System Prompt de clasificación una vez al inicializar
   - Almacenar en atributo de instancia para reutilización

3. Implementar método `_get_generation_config()`:
   - Retornar configuración de generación optimizada
   - Incluir `response_mime_type="application/json"` si el modelo lo soporta (Gemini 2.5 Flash y 1.5 Pro+)
   - Esto fuerza a Gemini a retornar JSON válido directamente

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`

### 3.3. Construcción Optimizada de Prompts

**Objetivo**: Construir prompts eficientes que minimicen tokens del usuario y maximicen uso del System Prompt.

**Tareas**:
1. Implementar método `_should_use_few_shot_examples()`:
   - Parámetros: `description: str`, `codcategoria: int`
   - **Objetivo**: Determinar si se deben usar ejemplos few-shot basándose en la complejidad de la solicitud
   - **Criterios para usar few-shot**:
     1. Descripción muy corta o ambigua (< 20 caracteres)
     2. Palabras clave que sugieren múltiples aplicaciones: "tanto", "como", "y también", "además", "ambas", "las dos", "amerika y dominio", "dominio y amerika", "ambos sistemas"
     3. Discrepancia potencial: Usuario menciona una aplicación pero categoría es otra (ej: menciona "Amerika" pero codcategoria=300)
     4. Ambigüedad en la descripción: "no sé", "no estoy seguro", "creo que", "tal vez", "ayuda", "problema", "error"
     5. Descripción muy larga (> 500 caracteres) - puede ser compleja
   - Retornar: `bool` (True si usar few-shot, False para prompt base)
   - **Optimización**: Esta decisión se toma ANTES de construir el prompt, evitando tokens innecesarios

2. Implementar método `_build_classification_prompt()`:
   - Parámetros: `description: str` (descripción de la solicitud), `codcategoria: int` (categoría seleccionada)
   - **Estrategia de optimización**:
     - **PASO 1**: Determinar complejidad con `_should_use_few_shot_examples()`
     - **PASO 2**: Seleccionar System Prompt apropiado:
       - Si `use_few_shot == True`: Usar `CLASSIFICATION_SYSTEM_PROMPT_WITH_EXAMPLES`
       - Si `use_few_shot == False`: Usar `CLASSIFICATION_SYSTEM_PROMPT_BASE`
     - **PASO 3**: Minimizar contenido del usuario: solo incluir `description` y `codcategoria` con su mapeo
     - NO incluir instrucciones repetidas del System Prompt (ya están en System Prompt)
     - Limitar longitud de descripción si es muy larga (ej: primeros 500 caracteres)
     - Mapear `codcategoria` a nombre de categoría para contexto:
       - `300` → "Cambio de Contraseña Cuenta Dominio"
       - `400` → "Cambio de Contraseña Amerika"
     - Formato del prompt final (optimizado para tokens):
       ```
       [System Prompt] (seleccionado según complejidad, cargado una vez al inicio, reutilizado)
       
       [User Message] (mínimo, solo contexto):
       Categoría: {codcategoria} ({nombre_categoria})
       Descripción: {description_sanitized}
       ```
     - NO incluir texto como "Clasifica esta solicitud" (ya está en System Prompt)
   - Retornar tupla: `(system_prompt: str, user_message_dict: dict)`
   - Registrar en logs qué tipo de prompt se usó (para métricas)

2. Implementar método `_sanitize_user_input()`:
   - Parámetros: `description: str`
   - Limitar longitud de descripción si es muy larga (ej: primeros 500 caracteres)
   - Eliminar caracteres innecesarios que consuman tokens
   - Retornar descripción optimizada

3. Implementar método `_estimate_tokens()` (opcional, para monitoreo):
   - Estimar tokens del prompt antes de enviar
   - Registrar en logs si excede umbral configurable
   - Útil para debugging y optimización

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`

### 3.4. Clasificación de Solicitudes con Respuesta JSON Estructurada

**Objetivo**: Implementar lógica de clasificación que garantice respuestas en formato JSON estructurado y validado, optimizando el uso de tokens y minimizando llamadas innecesarias.

**Mejores Prácticas de Optimización**:
- **System Prompt reutilizable**: Cargar una vez al inicio, no regenerar en cada solicitud (reduce ~200-300 tokens por solicitud)
- **Minimizar tokens del usuario**: Solo incluir descripción y categoría, no repetir instrucciones del System Prompt (reduce ~50-100 tokens)
- **JSON Mode**: Usar `response_mime_type="application/json"` si está disponible (Gemini 2.5 Flash y 1.5 Pro+) para garantizar respuestas JSON válidas
- **Temperatura baja**: 0.1-0.3 para respuestas consistentes y estructuradas (reduce variabilidad)
- **Límite de tokens de salida**: 500 tokens es suficiente para JSON de clasificación (reduce costo)
- **Una sola llamada**: Clasificación y extracción de parámetros en una sola llamada (evita ~500-800 tokens de segunda llamada)
- **Validación estricta**: Usar Pydantic para validar estructura JSON de respuesta (garantiza consistencia)

**Tareas**:
1. Implementar método `classify_request()`:
   - Parámetros: `description: str`, `codcategoria: int`, `ususolicita: str`
   - Sanitizar descripción con `_sanitize_user_input()`
   - Construir prompt optimizado con `_build_classification_prompt()`
   - Llamar a Gemini AI con:
     - System Prompt (cargado una vez al inicio, reutilizado para todas las solicitudes)
     - User message (solo descripción y categoría, minimizado y sanitizado)
     - Configuración de generación:
       - `response_mime_type="application/json"` (soportado en Gemini 2.5 Flash y 1.5 Pro+)
       - `temperature`: Desde settings (default: 0.2)
       - `max_output_tokens`: Desde settings (default: 500)
   - Parsear respuesta JSON de Gemini:
     - Si `response_mime_type="application/json"` está habilitado, la respuesta ya es JSON puro
     - Si no, intentar extraer JSON del texto (por si Gemini agrega texto adicional)
     - Validar que el JSON sea válido y parseable

2. Validar y parsear respuesta JSON:
   - Intentar parsear respuesta como JSON
   - Si falla, intentar extraer JSON del texto (por si Gemini agrega texto adicional)
   - Validar estructura contra `CLASSIFICATION_RESPONSE_SCHEMA`:
     - `app_type`: Debe ser "amerika" o "dominio"
     - `confidence`: Debe estar entre 0.0 y 1.0
     - `detected_actions`: Debe ser lista no vacía con valores válidos
     - `reasoning`: Debe ser string no vacío
     - `extracted_params`: Debe ser dict (opcional `user_name` para dominio)
     - `requires_secondary_app`: Debe ser bool (opcional, default: false)
     - `secondary_app_actions`: Debe ser lista de acciones válidas o null (requerido si requires_secondary_app=true)

3. Manejar respuestas inválidas:
   - Si JSON no es válido o estructura incorrecta:
     - Registrar error en logs
     - Retry con prompt más explícito (máximo 1 reintento)
     - Si falla definitivamente, usar valores por defecto seguros:
       - `app_type`: Basado en `codcategoria` (300→"dominio", 400→"amerika")
       - `confidence`: 0.5 (bajo, indica incertidumbre)
       - `detected_actions`: ["change_password"] (acción más común)
       - `reasoning`: "Clasificación automática por fallo en procesamiento de IA"

4. Crear estructura de datos `ClassificationResult`:
   ```python
   from pydantic import BaseModel, Field, field_validator
   from typing import Literal, List
   from datetime import datetime
   
   class ClassificationResult(BaseModel):
       app_type: Literal["amerika", "dominio"] = Field(
           ..., 
           description="Tipo de aplicación principal detectada"
       )
       confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza (0.0-1.0)")
       detected_actions: List[str] = Field(..., min_length=1, description="Acciones detectadas para app_type principal")
       reasoning: str = Field(..., max_length=200, description="Explicación de la clasificación")
       extracted_params: dict = Field(default_factory=dict, description="Parámetros extraídos")
       
       # Campos para soportar múltiples aplicaciones
       requires_secondary_app: Optional[bool] = Field(
           False,
           description="True si el usuario también requiere acciones en la otra aplicación"
       )
       secondary_app_actions: Optional[List[str]] = Field(
           None,
           description="Acciones requeridas para la aplicación secundaria (si requires_secondary_app=True)"
       )
       
       raw_classification: str = Field(..., description="Respuesta original de Gemini para auditoría")
       classification_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp ISO8601")
       
       @field_validator('detected_actions')
       @classmethod
       def validate_actions(cls, v):
           valid_actions = ["change_password", "unlock_account"]
           for action in v:
               if action not in valid_actions:
                   raise ValueError(f"Acción no válida: {action}")
           return v
       
       @field_validator('secondary_app_actions')
       @classmethod
       def validate_secondary_actions(cls, v, info):
           if v is not None:
               requires_secondary = info.data.get('requires_secondary_app', False)
               if requires_secondary and not v:
                   raise ValueError("secondary_app_actions no puede estar vacío si requires_secondary_app=True")
               valid_actions = ["change_password", "unlock_account"]
               for action in v:
                   if action not in valid_actions:
                       raise ValueError(f"Acción secundaria no válida: {action}")
           return v
   ```
   - Usar Pydantic para validación automática de tipos y valores
   - Retornar instancia de `ClassificationResult` validada
   - Si la validación falla, lanzar excepción descriptiva

5. Optimización de llamadas y tokens:
   - **NO cachear resultados** (cada solicitud es única, incluso con descripción similar)
   - **Una sola llamada por solicitud**: No hacer llamadas adicionales para extracción de parámetros (ya incluida en clasificación)
   - **Monitoreo de tokens**:
     - Registrar estimación de tokens usados (si está disponible en la API)
     - Alertar si excede umbral configurable (ej: >2000 tokens por solicitud)
     - Registrar métricas: tokens de entrada, tokens de salida, tiempo de respuesta
   - **Optimización continua**: Revisar logs periódicamente para identificar oportunidades de reducción de tokens

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`
- `agm-desk-ai/agent/prompts/system_prompts.py` (agregar schema de respuesta)

### 3.5. Manejo de Errores y Reintentos Optimizados con Try-Catch Completo

**Objetivo**: Manejar errores de Gemini de forma eficiente, minimizando reintentos innecesarios y consumo de tokens, con try-catch en todas las llamadas a la API.

**Tareas**:
1. **Implementar try-catch en `classify_request()`**:
   - Envolver todas las llamadas a Gemini API en try-catch
   - **Casos edge a manejar**:
     - `google.generativeai.types.APIError`: Error de API de Gemini (rate limit, quota, etc.)
     - `google.generativeai.types.InvalidResponseError`: Respuesta no válida o no parseable
     - `TimeoutError`: Timeout en la llamada
     - `ValueError`: Error al parsear JSON de respuesta
     - `KeyError`: Campo faltante en respuesta JSON esperada
     - `ConnectionError`: Error de conexión con Gemini API
     - `Exception`: Cualquier otro error inesperado
   - **Ejemplo de implementación**:
     ```python
     async def classify_request(
         self,
         description: str,
         codcategoria: int,
         ususolicita: str
     ) -> ClassificationResult:
         try:
             # Sanitizar y construir prompt
             sanitized_desc = self._sanitize_user_input(description)
             prompt = self._build_classification_prompt(sanitized_desc, codcategoria)
             
             # Llamar a Gemini API
             model = self._get_model()
             response = await model.generate_content_async(
                 prompt,
                 generation_config=self._get_generation_config()
             )
             
             # Parsear y validar respuesta
             classification_data = self._parse_classification_response(response)
             return ClassificationResult(**classification_data)
             
         except google.generativeai.types.APIError as e:
             error_code = getattr(e, 'code', None)
             
             # Rate limit: Reintentar una vez
             if error_code == 429 or "rate limit" in str(e).lower():
                 logger.warning("Rate limit de Gemini, reintentando...", attempt=1)
                 await asyncio.sleep(5)  # Esperar 5 segundos
                 try:
                     # Reintentar una vez
                     response = await model.generate_content_async(...)
                     classification_data = self._parse_classification_response(response)
                     return ClassificationResult(**classification_data)
                 except Exception:
                     # Si falla el reintento, usar fallback
                     logger.error("Reintento falló, usando fallback", error=str(e))
                     return self._get_fallback_classification(codcategoria, ususolicita)
             
             # Quota excedida: No reintentar, usar fallback
             elif error_code == 429 or "quota" in str(e).lower():
                 logger.error("Quota de Gemini excedida, usando fallback", error=str(e))
                 return self._get_fallback_classification(codcategoria, ususolicita)
             
             # Otros errores de API
             else:
                 logger.error("Error de API de Gemini", error_code=error_code, error=str(e))
                 return self._get_fallback_classification(codcategoria, ususolicita)
         
         except (ValueError, KeyError) as e:
             # Error al parsear JSON o estructura inválida
             logger.error("Error al parsear respuesta de Gemini", error=str(e))
             # Reintentar una vez con prompt más explícito
             try:
                 prompt_explicit = self._build_classification_prompt_explicit(sanitized_desc, codcategoria)
                 response = await model.generate_content_async(prompt_explicit, ...)
                 classification_data = self._parse_classification_response(response)
                 return ClassificationResult(**classification_data)
             except Exception:
                 logger.error("Reintento con prompt explícito falló, usando fallback")
                 return self._get_fallback_classification(codcategoria, ususolicita)
         
         except TimeoutError as e:
             logger.error("Timeout en llamada a Gemini", timeout=30.0, error=str(e))
             # Reintentar una vez con timeout mayor
             try:
                 response = await model.generate_content_async(..., timeout=60.0)
                 classification_data = self._parse_classification_response(response)
                 return ClassificationResult(**classification_data)
             except Exception:
                 logger.error("Reintento con timeout mayor falló, usando fallback")
                 return self._get_fallback_classification(codcategoria, ususolicita)
         
         except ConnectionError as e:
             logger.error("Error de conexión con Gemini API", error=str(e))
             return self._get_fallback_classification(codcategoria, ususolicita)
         
         except Exception as e:
             logger.error("Error inesperado en clasificación", error=str(e), exc_info=True)
             return self._get_fallback_classification(codcategoria, ususolicita)
     ```

2. **Implementar método `_get_fallback_classification()`**:
   - **Validar `codcategoria` primero**:
     - Si `codcategoria` NO es 300 ni 400:
       - NO usar fallback de clasificación
       - Lanzar excepción `InvalidCategoryError` o retornar `None` (la solicitud será ignorada, ver FASE 5.3, Paso 7.1.5)
     - **Referencia**: Ver FASE 4.1 (Servicio de Validación de Solicitudes) para validación de categoría antes de usar fallback
   - Si `codcategoria` es 300 o 400, usar clasificación basada en `codcategoria`:
     - `300` → `app_type: "dominio"`
     - `400` → `app_type: "amerika"`
   - `confidence: 0.5` (indica clasificación automática, no IA)
   - `detected_actions: ["change_password"]` (acción más común y segura)
   - `reasoning: "Clasificación automática por fallo en procesamiento de IA"`
   - `extracted_params: {}` (vacío, se usará `ususolicita` por defecto)
   - Registrar en logs que se usó fallback con severidad WARNING
   - Retornar `ClassificationResult` válido (no lanzar excepción)
   - **Mensaje amigable para el usuario** (incluir en `AI_CLASSIFICATION_DATA`):
     ```python
     {
         "fallback_used": True,
         "fallback_reason": "El sistema de clasificación inteligente no está disponible temporalmente",
         "user_message": "Su solicitud está siendo procesada con clasificación automática basada en la categoría seleccionada."
     }
     ```

3. **Métricas y monitoreo**:
   - Registrar tiempo de respuesta de Gemini
   - Registrar número de tokens usados (si está disponible en la API)
   - Registrar tasa de éxito/fallo de clasificaciones
   - Registrar número de fallbacks usados
   - Alertar si la tasa de fallo excede umbral (ej: >10%)
   - Alertar si la tasa de fallbacks excede umbral (ej: >5%)

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`

### 3.6. Validación y Corrección de Categoría

**Objetivo**: Validar que la categoría seleccionada por el usuario coincida con la clasificación de la IA.

**Tareas**:
1. Implementar método `validate_category()`:
   - Parámetros: `codcategoria: int`, `app_type: Literal["amerika", "dominio"]`
   - Mapeo de categorías:
     - `300` → "dominio" (Cambio de Contraseña Cuenta Dominio)
     - `400` → "amerika" (Cambio de Contraseña Amerika)
   - Comparar `codcategoria` con `app_type` detectado
   - Retornar `(is_valid: bool, corrected_codcategoria: Optional[int])`

2. Si la categoría no coincide:
   - Calcular `corrected_codcategoria` según `app_type` detectado
   - Registrar warning en logs
   - Retornar categoría corregida

3. Si la categoría coincide:
   - Retornar `is_valid=True, corrected_codcategoria=None`

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`

### 3.7. Extracción de Parámetros

**Objetivo**: Extraer parámetros necesarios para ejecutar acciones desde la descripción.

**Tareas**:
1. Implementar método `extract_parameters()`:
   - Parámetros: `description: str`, `app_type: Literal["amerika", "dominio"]`, `ususolicita: str`, `classification_result: Optional[ClassificationResult] = None`
   - Para `app_type == "dominio"`:
     - **Prioridad de `user_name`**: `extracted_params.user_name` (del `ClassificationResult`) > `ususolicita`
     - Si `classification_result` está presente y tiene `extracted_params.user_name`:
       - Validar formato de `user_name` extraído:
         - Solo caracteres alfanuméricos y guiones bajos
         - Máximo 25 caracteres
         - No vacío
       - Si es válido, usar `user_name` extraído
       - Si es inválido, usar `ususolicita` como fallback
     - Si `classification_result` no está presente o `extracted_params.user_name` está vacío:
       - Intentar extraer `user_name` de la descripción (procesamiento básico de texto)
       - Si se encuentra y es válido, usarlo
       - Si no se encuentra o es inválido, usar `ususolicita` como `user_name` por defecto
   - Para `app_type == "amerika"`:
     - Usar `ususolicita` como `user_id`
   - Retornar dict con parámetros extraídos:
     ```python
     {
         "user_id": ususolicita,  # Siempre presente
         "user_name": user_name   # Solo para dominio, validado según prioridad
     }
     ```

2. Optimización de extracción:
   - Preferir extracción desde `extracted_params` del `ClassificationResult` (ya procesado por Gemini)
   - Solo usar procesamiento de texto adicional si `extracted_params` está vacío
   - Evitar llamadas adicionales a Gemini para extracción (ya está incluida en clasificación)

3. Validación de `user_name` para Dominio:
   - En FASE 5.3, cuando se ejecute `find_user`:
     - Primero intentar con `user_name` extraído (si está presente y es válido)
     - Si no se encuentra, intentar con `ususolicita`
     - Si ninguno se encuentra, pedir aclaración al usuario (ver FASE 5.3, Paso 7.3)

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py`

### 3.8. Validación de Requisitos de Respuesta de IA Antes de Ejecutar Acciones (CRÍTICO)

**Objetivo**: Validar que la respuesta de la IA contenga todos los datos requeridos y correctos antes de ejecutar acciones en el backend. Esta validación es **CRÍTICA** y debe ejecutarse como primer paso después de la clasificación para garantizar que el agente funcione correctamente.

**Justificación**: La respuesta de Gemini AI puede contener datos incompletos, incorrectos o en formato no válido. Si no se validan estos datos antes de ejecutar acciones, el agente puede:
- Intentar ejecutar acciones con parámetros faltantes o inválidos
- Fallar en el backend con errores que podrían evitarse
- Generar mensajes de error confusos para el usuario
- Consumir recursos innecesariamente

**IMPORTANTE**: Esta validación debe ejecutarse **ANTES** de cualquier intento de ejecutar acciones en el backend (FASE 5.3, Paso 7.3). Si la validación falla, el agente NO debe ejecutar acciones y debe actualizar la solicitud con un mensaje de error claro.

**Tareas**:

1. **Crear método `validate_classification_for_execution()` en `AIProcessor`**:
   - Parámetros: `classification_result: ClassificationResult`, `ususolicita: str`
   - Retornar: `(is_valid: bool, errors: List[str], execution_params: dict)`
   - `execution_params` contiene los parámetros validados y mapeados listos para ejecutar acciones
   - **IMPORTANTE**: Este método debe validar tanto la aplicación principal como la secundaria (si aplica)

2. **Validaciones Requeridas para Amerika (`app_type == "amerika"`)**:
   
   a. **Validar `app_type`**:
      - Debe ser exactamente `"amerika"`
      - Si no coincide, agregar error: `f"app_type debe ser 'amerika', recibido: {classification_result.app_type}"`
   
   b. **Validar `detected_actions`**:
      - NO puede estar vacío
      - Debe contener solo valores válidos: `["change_password", "unlock_account"]`
      - Si contiene acciones inválidas, agregar error: `f"Acción no válida en detected_actions: {action}"`
   
   c. **Mapear acciones de IA a acciones del backend**:
      - **CRÍTICO**: La IA retorna `"change_password"` pero el backend de Amerika espera `"generate_password"`
      - Mapeo requerido:
        ```python
        action_mapping = {
            "change_password": "generate_password",  # Mapeo crítico
            "unlock_account": "unlock_account"        # Sin cambio
        }
        ```
      - Todas las acciones en `detected_actions` deben poder mapearse
      - Si una acción no puede mapearse, agregar error
   
   d. **Validar `user_id` (ususolicita)**:
      - NO puede estar vacío o ser `None`
      - Debe ser string no vacío después de `strip()`
      - Longitud máxima: 25 caracteres
      - Si falla, agregar error: `"ususolicita es requerido y no puede estar vacío"` o `"ususolicita no puede exceder 25 caracteres"`
   
   e. **Validar `confidence` (recomendado, no crítico)**:
      - Si `confidence < 0.5`, agregar warning (no error): `f"Confidence muy bajo ({confidence}), puede indicar clasificación incorrecta"`
      - Registrar warning en logs pero continuar procesamiento
   
   f. **Validar aplicación secundaria (si aplica)**:
      - Si `requires_secondary_app == True`:
        - Validar que `secondary_app_actions` NO esté vacío
        - Validar que todas las acciones en `secondary_app_actions` sean válidas: `["change_password", "unlock_account"]`
        - Si la aplicación secundaria es "dominio", validar que `user_name` esté disponible (usar mismo `user_name` de aplicación principal o `ususolicita`)

3. **Validaciones Requeridas para Dominio (`app_type == "dominio"`)**:
   
   a. **Validar `app_type`**:
      - Debe ser exactamente `"dominio"`
      - Si no coincide, agregar error: `f"app_type debe ser 'dominio', recibido: {classification_result.app_type}"`
   
   b. **Validar `detected_actions`**:
      - NO puede estar vacío
      - Debe contener solo valores válidos: `["change_password", "unlock_account"]`
      - Si contiene acciones inválidas, agregar error: `f"Acción no válida en detected_actions: {action}"`
   
   c. **Validar `user_id` (ususolicita)**:
      - NO puede estar vacío o ser `None`
      - Debe ser string no vacío después de `strip()`
      - Longitud máxima: 25 caracteres
      - Si falla, agregar error
   
   d. **Validar `user_name` (CRÍTICO para Dominio)**:
      - **Prioridad de extracción**:
        1. `classification_result.extracted_params.user_name` (si está presente y es válido)
        2. `ususolicita` (como fallback)
      - **Validación de formato**:
        - Debe coincidir con regex: `^[a-zA-Z0-9_]{1,25}$`
        - Solo caracteres alfanuméricos y guiones bajos
        - Longitud: 1-25 caracteres
        - NO puede estar vacío
      - Si `user_name` no es válido después de aplicar prioridad y validación:
        - Agregar error: `f"user_name tiene formato inválido: {user_name}. Debe ser alfanumérico con guiones bajos, máximo 25 caracteres"`
      - **NOTA**: `user_name` es requerido para ejecutar `find_user` y acciones posteriores en Dominio
   
   e. **Validar `confidence` (recomendado, no crítico)**:
      - Si `confidence < 0.5`, agregar warning (no error)
      - Registrar warning en logs pero continuar procesamiento
   
   f. **Validar aplicación secundaria (si aplica)**:
      - Si `requires_secondary_app == True`:
        - Validar que `secondary_app_actions` NO esté vacío
        - Validar que todas las acciones en `secondary_app_actions` sean válidas: `["change_password", "unlock_account"]`
        - Si la aplicación secundaria es "amerika", no requiere validación adicional de `user_name`

4. **Estructura de `execution_params` retornado**:
   
   **Para Amerika**:
   ```python
   {
       "mapped_actions": ["generate_password", "unlock_account"],  # Acciones mapeadas del backend
       "user_id": "mzuloaga"  # Validado y sanitizado
   }
   ```
   
   **Para Dominio**:
   ```python
   {
       "mapped_actions": ["change_password", "unlock_account"],  # Sin mapeo necesario
       "user_id": "jperez",  # Validado y sanitizado
       "user_name": "jperez"  # Validado, formato correcto
   }
   ```
   
   **Para Múltiples Aplicaciones (requires_secondary_app=True)**:
   ```python
   {
       "primary_app": "dominio",
       "primary_actions": ["change_password"],  # Acciones para app principal
       "requires_secondary_app": True,
       "secondary_app": "amerika",
       "secondary_app_actions": ["unlock_account"],  # Acciones para app secundaria (ya mapeadas si es Amerika)
       "user_id": "jperez",  # Validado y sanitizado
       "user_name": "jperez"  # Validado, formato correcto (requerido si dominio está presente)
   }
   ```

5. **Manejo de Errores de Validación**:
   - Si `is_valid == False`:
     - NO ejecutar acciones en el backend
     - Actualizar solicitud con mensaje de error claro:
       - `SOLUCION`: "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación. Por favor, contacte al soporte."
     - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de error
     - Agregar información en `AI_CLASSIFICATION_DATA`:
       ```python
       {
           "validation_failed": True,
           "validation_errors": errors,  # Lista de errores
           "validation_timestamp": datetime.utcnow().isoformat(),
           "error_details": {
               "error_type": "classification_validation_failed",
               "user_message": "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación.",
               "action_suggestion": "Por favor, contacte al soporte para asistencia."
           }
       }
       ```
     - Registrar errores en logs con severidad ERROR
     - Retornar inmediatamente (no continuar con ejecución de acciones)

6. **Implementación del método**:
   ```python
   def validate_classification_for_execution(
       self,
       classification_result: ClassificationResult,
       ususolicita: str,
       app_type: str
   ) -> tuple[bool, list[str], dict]:
       """
       Valida que la clasificación de IA tenga todos los datos necesarios
       antes de ejecutar acciones en el backend.
       
       CRÍTICO: Este método debe ejecutarse ANTES de cualquier intento
       de ejecutar acciones. Si falla, NO se deben ejecutar acciones.
       
       Returns:
           (is_valid, errors, execution_params)
       """
       errors = []
       execution_params = {}
       
       # Validar app_type
       if classification_result.app_type != app_type:
           errors.append(
               f"app_type no coincide: esperado '{app_type}', "
               f"recibido '{classification_result.app_type}'"
           )
           return False, errors, {}
       
       # Validar detected_actions
       if not classification_result.detected_actions:
           errors.append("detected_actions no puede estar vacío")
           return False, errors, {}
       
       valid_ai_actions = ["change_password", "unlock_account"]
       for action in classification_result.detected_actions:
           if action not in valid_ai_actions:
               errors.append(f"Acción no válida en detected_actions: {action}")
       
       # Validar user_id (ususolicita)
       if not ususolicita or not ususolicita.strip():
           errors.append("ususolicita es requerido y no puede estar vacío")
       elif len(ususolicita) > 25:
           errors.append("ususolicita no puede exceder 25 caracteres")
       
       # Validaciones específicas por app_type
       if app_type == "amerika":
           # Mapear acciones: change_password → generate_password
           action_mapping = {
               "change_password": "generate_password",
               "unlock_account": "unlock_account"
           }
           mapped_actions = []
           for ai_action in classification_result.detected_actions:
               if ai_action in action_mapping:
                   mapped_actions.append(action_mapping[ai_action])
               else:
                   errors.append(f"No se puede mapear acción para Amerika: {ai_action}")
           
           if not errors:
               execution_params = {
                   "mapped_actions": mapped_actions,
                   "user_id": ususolicita.strip()
               }
       
       elif app_type == "dominio":
           # Validar user_name (CRÍTICO)
           extracted_params = classification_result.extracted_params or {}
           user_name = extracted_params.get("user_name")
           
           # Prioridad: extracted_params.user_name > ususolicita
           if not user_name or not user_name.strip():
               user_name = ususolicita.strip()
           
           # Validar formato de user_name
           import re
           if not re.match(r'^[a-zA-Z0-9_]{1,25}$', user_name):
               errors.append(
                   f"user_name tiene formato inválido: '{user_name}'. "
                   f"Debe ser alfanumérico con guiones bajos, máximo 25 caracteres"
               )
           
           if not errors:
               execution_params = {
                   "mapped_actions": classification_result.detected_actions,  # Sin mapeo
                   "user_id": ususolicita.strip(),
                   "user_name": user_name
               }
       
       # Validar confidence (warning, no error)
       if classification_result.confidence < 0.5:
           logger.warning(
               "Confidence muy bajo en clasificación",
               confidence=classification_result.confidence,
               app_type=app_type,
               detected_actions=classification_result.detected_actions
           )
       
       is_valid = len(errors) == 0
       return is_valid, errors, execution_params
   ```

7. **Checklist de Validación (debe pasar TODOS los puntos)**:
   - [ ] `app_type` coincide con el esperado ("amerika" o "dominio")
   - [ ] `detected_actions` NO está vacío
   - [ ] Todas las acciones en `detected_actions` son válidas: `["change_password", "unlock_account"]`
   - [ ] `ususolicita` está presente, no vacío, y tiene máximo 25 caracteres
   - [ ] Para Amerika: Todas las acciones pueden mapearse correctamente (`change_password` → `generate_password`)
   - [ ] Para Dominio: `user_name` está presente y tiene formato válido (alfanumérico + guiones bajos, 1-25 caracteres)
   - [ ] `confidence >= 0.5` (recomendado, genera warning si es menor pero no bloquea)

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/ai_processor.py` (agregar método `validate_classification_for_execution()`)

**Referencias**:
- Este método será llamado en FASE 5.3, Paso 7.1.6 (Validación de Requisitos de Respuesta de IA)
- Ver FASE 2.2 y 2.3 para requisitos de parámetros del backend
- Ver FASE 5.3, Paso 7.3 para uso de `execution_params` en ejecución de acciones

---

## FASE 4: Validación y Rate Limiting (request_validator.py)

**Justificación**: Implementar validación robusta y protección contra abusos antes de procesar solicitudes. Esto previene procesamiento de solicitudes inválidas o que excedan límites.

### 4.1. Servicio de Validación de Solicitudes

**Objetivo**: Crear servicio para validar y sanitizar datos de solicitudes recibidas.

**Tareas**:
1. Crear clase `RequestValidator` en `agent/services/request_validator.py`:
   - Inicializar con `settings: Settings`
   - Crear cliente de Supabase para consultas

2. Implementar método `validate_request_data()`:
   - Parámetros: `request_data: dict` (datos del evento Realtime)
   - Validar campos requeridos:
     - `codpeticiones`: Debe ser entero positivo
     - `codcategoria`: Debe ser entero válido (300 o 400)
     - `description`: Debe ser string no vacío
     - `ususolicita`: Debe ser string no vacío, máximo 25 caracteres
     - `codestado`: Debe ser 1 (PENDIENTE)
   - Retornar `(is_valid: bool, errors: List[str])`

3. Implementar método `sanitize_description()`:
   - Parámetros: `description: str`
   - Eliminar espacios en blanco al inicio y final
   - Normalizar espacios múltiples a uno solo
   - Validar longitud: `MIN_DESCRIPTION_LENGTH <= len <= MAX_DESCRIPTION_LENGTH`
   - Validar caracteres: Rechazar caracteres de control (excepto `\n`, `\r`, `\t`)
   - Retornar descripción sanitizada o lanzar excepción si es inválida

4. Implementar método `validate_category()`:
   - Parámetros: `codcategoria: int`
   - Verificar que sea 300 (Dominio) o 400 (Amerika)
   - Consultar en Supabase si la categoría existe (validación adicional)
   - Retornar `(is_valid: bool, error_message: Optional[str])`

5. Implementar método `validate_user()`:
   - Parámetros: `ususolicita: str`
   - Validar formato: Solo caracteres alfanuméricos y guiones bajos, máximo 25 caracteres
   - Validar que no esté vacío
   - Retornar `(is_valid: bool, error_message: Optional[str])`

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/request_validator.py` (nuevo)

### 4.2. Rate Limiting por Usuario

**Objetivo**: Implementar límites de solicitudes por usuario para prevenir abusos.

**Tareas**:
1. Implementar método `check_rate_limit()`:
   - Parámetros: `ususolicita: str`, `codcategoria: int`
   - Consultar en Supabase solicitudes del usuario en la ventana de tiempo:
     ```sql
     SELECT COUNT(*) 
     FROM HLP_PETICIONES 
     WHERE USUSOLICITA = ususolicita 
       AND CODCATEGORIA IN (300, 400)  -- Solo cambio de contraseña
       AND FESOLICITA >= NOW() - INTERVAL '{RATE_LIMIT_WINDOW_HOURS} hours'
       AND CODESTADO IN (1, 2, 3)  -- Todas las solicitudes (pendientes, en trámite, solucionadas)
     ```
   - Comparar con `MAX_REQUESTS_PER_USER`
   - Retornar `(within_limit: bool, current_count: int, limit: int, window_hours: int)`

2. Implementar método `get_rate_limit_info()`:
   - Parámetros: `ususolicita: str`
   - Retornar información detallada del rate limit:
     - Número de solicitudes actuales en la ventana
     - Límite máximo configurado
   - Ventana de tiempo restante hasta que se reinicie el contador
   - Útil para mensajes de error informativos

3. Manejar casos especiales:
   - Si el usuario excede el límite, NO procesar la solicitud
   - Actualizar solicitud con mensaje de error claro
   - Registrar evento en logs para auditoría

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/request_validator.py`

### 4.3. Validación de Tiempo de Procesamiento

**Objetivo**: Validar que las solicitudes no sean demasiado antiguas para procesar.

**Tareas**:
1. Implementar método `validate_request_age()`:
   - Parámetros: `fesolicita: datetime`, `max_age_hours: Optional[int] = None`
   - Calcular edad de la solicitud desde `fesolicita`
   - Si `max_age_hours` está configurado y la solicitud es más antigua:
     - Retornar `(is_valid: False, reason: "Solicitud demasiado antigua")`
   - Si no hay límite de edad o está dentro del límite:
     - Retornar `(is_valid: True, reason: None)`

2. Configurar límite de edad (opcional):
   - Agregar `MAX_REQUEST_AGE_HOURS: Optional[int]` a Settings (default: `None` - sin límite)
   - Si está configurado, rechazar solicitudes más antiguas que el límite
   - Útil para evitar procesar solicitudes muy antiguas que ya no son relevantes

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/request_validator.py`
- `agm-desk-ai/agent/core/config.py` (agregar `MAX_REQUEST_AGE_HOURS`)

### 4.4. Generación de Mensajes de Error para Usuario

**Objetivo**: Generar mensajes claros y profesionales cuando una solicitud es rechazada.

**Tareas**:
1. Implementar método `generate_rejection_message()`:
   - Parámetros: `rejection_reason: str`, `rate_limit_info: Optional[dict] = None`
   - Generar mensajes según el motivo de rechazo:
     - **Rate Limit Excedido**: 
       ```
       "Ha alcanzado el límite de solicitudes permitidas. 
       Puede crear hasta {limit} solicitudes de cambio de contraseña o desbloqueo 
       cada {window_hours} horas. 
       Actualmente tiene {current_count} solicitudes en la última ventana de tiempo.
       Por favor, intente nuevamente después de {time_remaining}."
       ```
     - **Descripción Inválida**:
       ```
       "La descripción de su solicitud no cumple con los requisitos. 
       Debe tener entre {min_length} y {max_length} caracteres y contener información relevante."
       ```
     - **Categoría Inválida**:
       ```
       "La categoría seleccionada no es válida para este tipo de solicitud."
       ```
     - **Solicitud Demasiado Antigua**:
       ```
       "Esta solicitud es demasiado antigua para ser procesada automáticamente. 
       Por favor, cree una nueva solicitud."
       ```
   - Retornar mensaje formateado

2. Integrar mensajes en actualización de solicitud:
   - Cuando una solicitud es rechazada, actualizar `SOLUCION` con el mensaje de error
   - Establecer `CODESTADO = 3` (SOLUCIONADO) pero con mensaje de rechazo
   - Establecer `CODUSOLUCION = "AGENTE-MS"`
   - Agregar información de rechazo en `AI_CLASSIFICATION_DATA`:
     ```python
     {
         "rejected": True,
         "rejection_reason": "...",
         "rejection_timestamp": datetime.utcnow().isoformat(),
         "rate_limit_info": {...}  # Si aplica
     }
     ```

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/request_validator.py`

**Nota sobre Validación en el Backend**: Aunque el agente AI tiene filtros de seguridad robustos, se recomienda implementar validación básica de seguridad también en el backend FastAPI antes de guardar solicitudes. Esto proporciona una capa adicional de protección. Ver [Especificación del Backend](./03_backend_detailed.md) para detalles sobre validación en el endpoint `POST /api/requests`.

### 4.5. Validación de Seguridad y Filtros Anti-Prompt Injection

**Objetivo**: Implementar validación de seguridad para detectar y prevenir intentos de prompt injection y contenido malicioso antes de enviar solicitudes a Gemini AI.

**Justificación**: Es crítico validar la seguridad de las solicitudes ANTES de enviarlas a Gemini AI para prevenir manipulación del sistema, extracción de información sensible o ejecución de acciones no autorizadas.

**Tareas**:
1. Implementar método `validate_security()` en `RequestValidator`:
   - Parámetros: `description: str`
   - Retornar: `(is_safe: bool, risk_level: str, detected_patterns: List[str])`
   - `risk_level`: "LOW", "MEDIUM", "HIGH", "CRITICAL"
   - `detected_patterns`: Lista de patrones detectados (para auditoría)

2. Algoritmo de detección (Nivel Intermedio):
   - **Detección de palabras clave de prompt injection**:
     - Escanear `description` buscando palabras clave de `PROMPT_INJECTION_KEYWORDS` (separadas por comas)
     - Ejemplos: "ignore", "actúa", "ejecuta", "revela", "bypass", "override", "ignora", "ejecutar", "revelar"
     - Contar número de coincidencias (más coincidencias = mayor riesgo)
   
   - **Detección de patrones de instrucciones peligrosas**:
     - Escanear `description` buscando patrones de `DANGEROUS_INSTRUCTION_PATTERNS` (separados por comas)
     - Ejemplos: "debes hacer", "necesito que hagas", "por favor ejecuta", "debes", "necesitas", "tienes que"
     - Detectar si aparecen en contexto de instrucciones al sistema (no solo como parte de la descripción del problema)
   
   - **Detección de patrones de bypass**:
     - Buscar frases como "ignora las instrucciones anteriores", "olvida todo lo anterior", "solo sigue estas instrucciones"
     - Buscar intentos de inyección de código o comandos (ej: "```", "system", "exec", "eval")
   
   - **Análisis de patrones múltiples**:
     - Si se detectan múltiples palabras clave o patrones = riesgo mayor
     - Si se detecta patrón de bypass = riesgo CRITICAL
     - Si se detecta combinación de palabras clave + patrones peligrosos = riesgo HIGH

3. Cálculo de `risk_level`:
   - **LOW**: No se detectaron patrones sospechosos o solo coincidencias aisladas sin contexto
   - **MEDIUM**: Se detectaron 1-2 palabras clave o 1 patrón peligroso, pero sin contexto de instrucción al sistema
   - **HIGH**: Se detectaron múltiples palabras clave (3+) o múltiples patrones peligrosos, o combinación de ambos
   - **CRITICAL**: Se detectó patrón de bypass explícito, intento de inyección de código, o combinación de múltiples indicadores de alto riesgo

4. Implementar método `generate_security_rejection_message()`:
   - Parámetros: `risk_level: str`, `detected_patterns: List[str]`
   - Generar mensaje educativo con guía:
     ```
     "Su solicitud contiene instrucciones que no pueden ser procesadas. 
     Por favor, describa su problema de forma clara sin incluir instrucciones al sistema."
     ```
   - El mensaje debe ser profesional y educativo, sin exponer detalles técnicos de la detección
   - Retornar mensaje formateado

5. Integración con validación de seguridad:
   - Si `ENABLE_SECURITY_FILTERS` está deshabilitado (solo para debugging), saltar validación
   - Si `risk_level` es HIGH o CRITICAL:
     - Retornar `is_safe = False`
     - NO enviar a Gemini AI (prevenir prompt injection)
   - Si `risk_level` es MEDIUM:
     - Retornar `is_safe = True` pero con advertencia
     - Registrar warning en logs
     - Continuar procesamiento con precaución
   - Si `risk_level` es LOW:
     - Retornar `is_safe = True`
     - Continuar procesamiento normalmente

6. Registro y auditoría:
   - Registrar todos los casos donde `is_safe = False` con severidad ALTA/CRÍTICA
   - Incluir en logs: `risk_level`, `detected_patterns`, `description` (sanitizada), `ususolicita`
   - NO loggear la descripción completa si contiene contenido sensible (solo patrones detectados)

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/request_validator.py`

**Referencias**:
- Este método será utilizado en FASE 5.3 (Procesamiento de Nuevas Solicitudes) para validar seguridad antes de enviar a Gemini AI
- Ver FASE 5.3, punto 3 (Validación de Seguridad) para el uso completo de estos métodos

---

## FASE 5: Listener de Realtime (realtime_listener.py)

**Justificación**: Implementar el listener de Realtime después de tener el procesamiento de IA y ejecutor de acciones listos.

### 5.1. Configuración de Cliente Supabase

**Objetivo**: Configurar cliente de Supabase con service_role_key para bypass de RLS.

**Tareas**:
1. Crear clase `RealtimeListener` en `agent/services/realtime_listener.py`:
   - Inicializar con `settings: Settings`
   - Crear cliente de Supabase usando `create_client()`:
     ```python
     from supabase import create_client
     supabase = create_client(
         settings.SUPABASE_URL,
         settings.SUPABASE_SERVICE_ROLE_KEY
     )
     ```

2. Verificar conexión a Supabase:
   - Intentar consulta simple a tabla `HLP_PETICIONES`
   - Lanzar excepción si la conexión falla
   - Registrar log detallado de conexión exitosa:
     ```python
     logger.info(
         "Conexión a Supabase establecida exitosamente",
         supabase_url=settings.SUPABASE_URL,
         table="HLP_PETICIONES",
         service_role_configured=bool(settings.SUPABASE_SERVICE_ROLE_KEY)
     )
     ```

3. **Validar capacidad de escucha de eventos (CRÍTICO - Validación Temprana)**:
   - Verificar que Realtime esté habilitado en Supabase
   - Registrar log informativo sobre configuración de suscripción ANTES de intentar suscribirse:
     ```python
     logger.info(
         "Preparando suscripción a eventos Realtime",
         table="HLP_PETICIONES",
         event_type="INSERT",
         filter_state="CODESTADO = 1 (PENDIENTE)",
         supabase_realtime_enabled=True
     )
     ```
   - Este log debe aparecer ANTES de intentar suscribirse para validar que el agente está preparado para escuchar eventos

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/realtime_listener.py`

### 5.2. Suscripción a Eventos Realtime con Try-Catch Completo

**Objetivo**: Suscribirse a eventos INSERT en la tabla HLP_PETICIONES con manejo robusto de errores.

**Tareas**:
1. **Implementar método `subscribe_to_new_requests()` con try-catch y logs de validación**:
   - Suscribirse a cambios en tabla `HLP_PETICIONES`
   - Filtrar solo eventos de tipo `INSERT`
   - Filtrar solo solicitudes con `CODESTADO = 1` (PENDIENTE)
   - **Envolver suscripción en try-catch con logs detallados**:
     ```python
     async def subscribe_to_new_requests(self):
         try:
             # Log antes de suscribirse
             logger.info(
                 "Iniciando suscripción a eventos Realtime de Supabase",
                 table="HLP_PETICIONES",
                 event_type="INSERT",
                 filter_condition="CODESTADO = 1 (PENDIENTE)"
             )
             
             # Crear suscripción
             subscription = self.supabase.table("HLP_PETICIONES")\
                 .on("INSERT", self._handle_new_request)\
                 .subscribe()
             
             # Log detallado cuando se establece la suscripción exitosamente
             logger.info(
                 "✅ Suscripción a eventos Realtime establecida exitosamente",
                 table="HLP_PETICIONES",
                 event_type="INSERT",
                 subscription_active=True,
                 message="El agente está escuchando nuevos eventos de creación de solicitudes"
             )
             
             # Log de consola para validación temprana (visible inmediatamente)
             print("\n" + "="*70)
             print("🔔 AGENTE AI - LISTENER ACTIVO")
             print("="*70)
             print(f"📊 Tabla: HLP_PETICIONES")
             print(f"📥 Evento: INSERT")
             print(f"🔍 Filtro: CODESTADO = 1 (PENDIENTE)")
             print(f"✅ Estado: ESCUCHANDO eventos de creación de solicitudes")
             print("="*70 + "\n")
             
             return subscription
             
         except Exception as e:
             logger.error(
                 "❌ Error al crear suscripción Realtime",
                 table="HLP_PETICIONES",
                 error=str(e),
                 error_type=type(e).__name__,
                 exc_info=True
             )
             # Log de consola para error visible
             print("\n" + "="*70)
             print("❌ ERROR: No se pudo establecer suscripción a eventos Realtime")
             print(f"   Error: {str(e)}")
             print("="*70 + "\n")
             # Reintentar con backoff exponencial
             await self._retry_subscription()
     ```

2. **Configurar callback para procesar nuevos eventos con try-catch y log de validación inmediato**:
   - Callback debe recibir payload del evento
   - Extraer datos de la solicitud del payload
   - **CRÍTICO: Registrar log inmediato cuando se recibe un evento (PRIMER PASO - Validación de escucha)**:
     ```python
     async def _handle_new_request(self, payload):
         # LOG INMEDIATO - Validación de que el evento fue recibido (PRIMER PASO)
         from datetime import datetime
         event_timestamp = datetime.utcnow().isoformat()
         request_data = payload.get("new", {})
         codpeticiones = request_data.get("CODPETICIONES")
         
         # Log estructurado para debugging
         logger.info(
             "🎯 EVENTO RECIBIDO - Nueva solicitud detectada",
             codpeticiones=codpeticiones,
             event_timestamp=event_timestamp,
             table="HLP_PETICIONES",
             event_type="INSERT",
             payload_keys=list(request_data.keys()) if request_data else [],
             ususolicita=request_data.get("USUSOLICITA"),
             codcategoria=request_data.get("CODCATEGORIA"),
             codestado=request_data.get("CODESTADO")
         )
         
         # Log de consola para validación rápida (visible inmediatamente)
         print(f"\n[EVENTO RECIBIDO] Solicitud #{codpeticiones} detectada a las {event_timestamp}")
         print(f"   Usuario: {request_data.get('USUSOLICITA', 'N/A')}")
         print(f"   Categoría: {request_data.get('CODCATEGORIA', 'N/A')}")
         print(f"   Estado: {request_data.get('CODESTADO', 'N/A')} (PENDIENTE)\n")
         
         try:
             # Validar que tenga campos requeridos
             if not self._validate_request_payload(request_data):
                 logger.warning("Payload de solicitud inválido", payload=request_data)
                 return
             
             # Procesar solicitud (ver FASE 5.3: Procesamiento de Nuevas Solicitudes)
             await self.process_new_request(request_data)
             
         except Exception as e:
             logger.error(
                 "Error al procesar nueva solicitud",
                 codpeticiones=codpeticiones,
                 error=str(e),
                 exc_info=True
             )
             # NO lanzar excepción para no detener el listener
             # Actualizar solicitud con mensaje de error si es posible
             await self._handle_processing_error(request_data, e)
     ```

3. **Manejar reconexión automática con circuit breaker**:
   - Detectar desconexiones del WebSocket
   - Reintentar conexión con backoff exponencial
   - Implementar circuit breaker para evitar reintentos infinitos
   - Registrar eventos de conexión/desconexión en logs
   - **Ejemplo de implementación**:
     ```python
     async def _retry_subscription(self, max_retries: int = 5, initial_delay: float = 5.0):
         delay = initial_delay
         for attempt in range(max_retries):
             try:
                 await asyncio.sleep(delay)
                 subscription = await self.subscribe_to_new_requests()
                 logger.info("Reconexión exitosa", attempt=attempt + 1)
                 return subscription
             except Exception as e:
                 logger.warning("Reintento de suscripción falló", attempt=attempt + 1, error=str(e))
                 delay *= 2  # Backoff exponencial
                 if attempt == max_retries - 1:
                     logger.error("No se pudo establecer suscripción después de todos los reintentos")
                     raise
     ```

4. **Manejar errores de suscripción con try-catch**:
   - `ConnectionError`: Error de conexión con Supabase
   - `SubscriptionError`: Error al crear suscripción
   - `TimeoutError`: Timeout en la conexión
   - `ValueError`: Error al parsear payload
   - Retry automático con límite de intentos
   - **Mensajes amigables para logs**:
     ```python
     ERROR_MESSAGES = {
         ConnectionError: "No se pudo conectar con Supabase Realtime. Reintentando...",
         SubscriptionError: "Error al crear suscripción. Reintentando...",
         TimeoutError: "Timeout al establecer conexión. Reintentando...",
         ValueError: "Error al procesar datos de la suscripción."
     }
     ```

5. **Manejar errores de actualización en Supabase**:
   - Si falla actualizar solicitud, registrar en logs
   - Reintentar actualización con backoff exponencial
   - Si falla definitivamente, mantener en cola local para sincronización posterior
   - **Ejemplo**:
     ```python
     async def update_request(self, codpeticiones: int, updates: dict):
         try:
             result = self.supabase.table("HLP_PETICIONES")\
                 .update(updates)\
                 .eq("CODPETICIONES", codpeticiones)\
                 .execute()
             return result
         except Exception as e:
             logger.error(
                 "Error al actualizar solicitud en Supabase",
                 codpeticiones=codpeticiones,
                 error=str(e)
             )
             # Agregar a cola local para reintento posterior
             await self._add_to_retry_queue(codpeticiones, updates)
             raise
     ```

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/realtime_listener.py`

**Nota**: El SDK de Supabase para Python puede usar diferentes métodos para Realtime. Verificar documentación actualizada de `supabase-py` para la API correcta de suscripciones.

### 5.3. Procesamiento de Nuevas Solicitudes

**Objetivo**: Procesar nuevas solicitudes detectadas por Realtime con validación completa.

**Tareas**:
1. Implementar método `process_new_request()`:
   - Parámetros: `request_data: dict` (datos de la solicitud del evento)
   - Extraer campos relevantes:
     - `codpeticiones`: ID de la solicitud
     - `codcategoria`: Categoría seleccionada
     - `description`: Descripción del problema
     - `ususolicita`: Usuario que solicita
     - `codestado`: Estado (debe ser 1-PENDIENTE)
     - `fesolicita`: Fecha de creación

2. **Validación Inicial (Usar RequestValidator)**:
   - Llamar a `RequestValidator.validate_request_data()` para validar estructura
   - Si hay errores de validación:
     - Actualizar solicitud con mensaje de error
     - Registrar en logs y retornar (no procesar)
   - Llamar a `RequestValidator.sanitize_description()` para sanitizar descripción
   - Llamar a `RequestValidator.validate_category()` para validar categoría
   - Llamar a `RequestValidator.validate_user()` para validar usuario

3. **Validación de Seguridad (CRÍTICO - Antes de enviar a IA)**:
   - **Referencia**: Ver FASE 4.5 (Validación de Seguridad y Filtros Anti-Prompt Injection) para detalles de implementación
   - Llamar a `RequestValidator.validate_security(description)` para detectar:
     - Intentos de prompt injection
     - Instrucciones peligrosas al asistente
     - Contenido malicioso
   - Si `is_safe == False` y `risk_level` es `HIGH` o `CRITICAL`:
     - NO enviar a Gemini AI (prevenir prompt injection)
     - Generar mensaje de rechazo con `RequestValidator.generate_security_rejection_message()`
     - Actualizar solicitud con mensaje de rechazo
     - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de rechazo
     - Agregar información de seguridad en `AI_CLASSIFICATION_DATA`
     - Registrar en logs con severidad ALTA/CRÍTICA para auditoría
     - Retornar (NO procesar la solicitud)
   - Si `risk_level` es `MEDIUM`:
     - Registrar warning en logs
     - Continuar procesamiento pero agregar flag de advertencia
     - Enviar a Gemini AI con precaución (puede requerir prompt hardening adicional)

4. **Validación de Rate Limiting**:
   - Llamar a `RequestValidator.check_rate_limit(ususolicita, codcategoria)`
   - Si el usuario excede el límite:
     - Obtener información de rate limit con `RequestValidator.get_rate_limit_info()`
     - Generar mensaje de rechazo con `RequestValidator.generate_rejection_message()`
     - Actualizar solicitud con mensaje de rechazo (ver FASE 4.4)
     - Registrar evento en logs para auditoría
     - Retornar (no procesar la solicitud)

5. **Validación de Edad de Solicitud**:
   - Llamar a `RequestValidator.validate_request_age(fesolicita)`
   - Si la solicitud es demasiado antigua:
     - Generar mensaje de rechazo
     - Actualizar solicitud con mensaje de rechazo
     - Registrar en logs y retornar (no procesar)

6. **Actualizar Estado a TRAMITE con Feedback Inicial**:
   - Si todas las validaciones pasan, actualizar `CODESTADO = 2` (TRAMITE)
   - **Actualizar `SOLUCION` con mensaje informativo inicial**:
     - "Su solicitud está siendo procesada. El sistema está analizando su solicitud..."
   - **Agregar información de progreso en `AI_CLASSIFICATION_DATA`**:
     ```python
     {
         "processing_status": "validated",
         "current_step": "Clasificando solicitud con inteligencia artificial...",
         "progress_percentage": 10,
         "last_update": datetime.utcnow().isoformat()
     }
     ```
   - Esto proporciona feedback inmediato al usuario de que su solicitud está siendo atendida

7. **Orquestar Procesamiento Completo con Feedback Progresivo**:
   - **Paso 7.1: Clasificación con IA** (actualizar progreso al 30%):
     - Actualizar `SOLUCION`: "Analizando su solicitud con inteligencia artificial para determinar el tipo de aplicación y acciones necesarias..."
     - Actualizar `AI_CLASSIFICATION_DATA.processing_status = "classifying"`
     - Actualizar `AI_CLASSIFICATION_DATA.progress_percentage = 30`
     - Llamar a `AIProcessor.classify_request()` para clasificar (solo si pasó validación de seguridad)
       - **Optimización de tokens**: El System Prompt ya está cargado y reutilizado (no se regenera en cada solicitud)
       - **Minimización de contexto**: Solo se envía la descripción del usuario como contexto mínimo (descripción + categoría)
       - **Respuesta estructurada**: La respuesta se estructura en JSON validado con Pydantic `ClassificationResult`
       - **Una sola llamada**: No se hacen llamadas adicionales a Gemini (todo en una sola clasificación)
     - Después de clasificar, actualizar `AI_CLASSIFICATION_DATA` con resultados de clasificación:
       - Incluir `original_codcategoria: codcategoria` (categoría original seleccionada por el usuario)
       - Incluir `category_corrected: false` (se actualizará si hay discrepancia)
       - Incluir `corrected_codcategoria: null` (se actualizará si hay discrepancia)
   
   - **Paso 7.1.5: Detección y Corrección de Categoría (DESPUÉS de clasificación)**:
     - **OBJETIVO**: Detectar si hay discrepancia entre la categoría seleccionada por el usuario y el `app_type` detectado por la IA, y corregir la categoría si es necesario.
     - **IMPORTANTE**: La categoría es importante y debe ser correcta. Si el usuario la selecciona mal, el agente debe corregirla automáticamente.
     - **Mapeo de categorías**:
       - `app_type == "dominio"` → `CODCATEGORIA` correcto = `300`
       - `app_type == "amerika"` → `CODCATEGORIA` correcto = `400`
     - **Lógica de detección de discrepancia**:
       - Comparar `codcategoria` original con el `app_type` detectado:
         - Si `codcategoria == 300` y `app_type == "dominio"` → ✅ Coincide, no corregir
         - Si `codcategoria == 400` y `app_type == "amerika"` → ✅ Coincide, no corregir
         - Si `codcategoria == 300` y `app_type == "amerika"` → ❌ Discrepancia, corregir a `400`
         - Si `codcategoria == 400` y `app_type == "dominio"` → ❌ Discrepancia, corregir a `300`
     - **Si hay discrepancia**:
       - Calcular `corrected_codcategoria`:
         - Si `app_type == "dominio"` → `corrected_codcategoria = 300`
         - Si `app_type == "amerika"` → `corrected_codcategoria = 400`
       - **Actualizar `CODCATEGORIA` en Supabase** al valor correcto:
         ```python
         await self.update_request(codpeticiones, {
             "CODCATEGORIA": corrected_codcategoria
         })
         ```
       - **Actualizar `AI_CLASSIFICATION_DATA`**:
         - `category_corrected: true`
         - `corrected_codcategoria: corrected_codcategoria`
         - `original_codcategoria: codcategoria` (mantener original para auditoría)
       - **Registrar en logs**:
         ```python
         logger.info(
             "Categoría corregida automáticamente",
             codpeticiones=codpeticiones,
             original_codcategoria=codcategoria,
             corrected_codcategoria=corrected_codcategoria,
             app_type_detected=classification_result.app_type,
             reasoning=classification_result.reasoning
         )
         ```
       - **Ejemplo**: Usuario selecciona categoría 300 (dominio) pero menciona "Amerika" en descripción:
         - IA detecta: `app_type = "amerika"`
         - Sistema corrige: `CODCATEGORIA = 400`
         - Se ejecuta acción en Amerika
         - Categoría queda corregida en la solicitud
     - **Si NO hay discrepancia**:
       - `category_corrected: false`
       - `corrected_codcategoria: null`
       - `original_codcategoria: codcategoria`
       - Continuar con procesamiento normal
   
   - **Paso 7.1.5.1: Validación de Categoría para Procesamiento Automático (DESPUÉS de corrección)**:
     - Verificar si `codcategoria` (original o corregido) es 300 o 400:
       - Si NO es 300 ni 400:
         - **El agente debe IGNORAR la solicitud completamente** (no procesarla automáticamente, no ejecutar acciones)
         - **La clasificación con IA ya se ejecutó en el paso 7.1** (si pasó validación de seguridad del paso 3)
         - **Mantener la respuesta completa de clasificación de la IA** en `AI_CLASSIFICATION_DATA` (preservar `app_type`, `confidence`, `detected_actions`, `reasoning`, `extracted_params`, `raw_classification`, `classification_timestamp`, etc.)
         - **NO cambiar `CODESTADO`** (mantener el estado original: si estaba en PENDIENTE, mantener PENDIENTE; NO actualizar a TRAMITE ni a SOLUCIONADO)
         - **NO rechazar la solicitud** (no establecer mensaje de rechazo en `SOLUCION`, dejar `SOLUCION` sin modificar)
         - **NO actualizar ningún otro campo** de la solicitud excepto `AI_CLASSIFICATION_DATA`
         - Actualizar `AI_CLASSIFICATION_DATA` con estructura completa (ver subsección 5.4.1):
           - Agregar campos: `ignored: True`, `ignore_reason: "Categoría no soportada para procesamiento automático"`, `requires_human_review: True`, `auto_processing_skipped: True`, `ignored_at: timestamp`
           - Cambiar `processing_status: "ignored"`, `current_step: "Solicitud clasificada pero requiere atención humana"`, `progress_percentage: 100`
         - **La solicitud quedará para atención humana** (asistente humano la procesará manualmente)
         - **NO ejecutar acciones** (solo clasificar con IA y guardar resultado, sin ejecutar acciones técnicas)
         - Registrar en logs que la solicitud fue ignorada por categoría no válida (para auditoría)
         - Retornar inmediatamente (no continuar con ejecución de acciones, no actualizar estado)
       - Si es 300 o 400 (original o corregido):
         - Continuar con procesamiento normal (ir al paso 7.1.6)
   
   - **Paso 7.1.6: Validación de Requisitos de Respuesta de IA (CRÍTICO - PRIMER PASO ANTES DE EJECUTAR)**:
     - **OBJETIVO**: Validar que la respuesta de la IA contenga todos los datos requeridos y correctos antes de ejecutar acciones.
     - **JUSTIFICACIÓN**: Esta validación es CRÍTICA y debe ejecutarse como PRIMER PASO después de la clasificación para garantizar que el agente funcione correctamente. Si falla, NO se deben ejecutar acciones.
     - **Referencia**: Ver FASE 3.8 (Validación de Requisitos de Respuesta de IA Antes de Ejecutar Acciones) para detalles completos de implementación.
     - Actualizar `SOLUCION`: "Validando requisitos de la clasificación antes de ejecutar acciones..."
     - Actualizar `AI_CLASSIFICATION_DATA.processing_status = "validating_requirements"`
     - Actualizar `AI_CLASSIFICATION_DATA.progress_percentage = 45`
     - Llamar a `AIProcessor.validate_classification_for_execution()`:
       - Parámetros: `classification_result`, `ususolicita`
       - Este método valida:
         - `app_type` es válido ("amerika" o "dominio")
         - `detected_actions` no está vacío y contiene solo acciones válidas
         - `ususolicita` está presente y es válido
         - Para Amerika: Mapea `change_password` → `generate_password`
         - Para Dominio: Valida y extrae `user_name` con formato correcto
         - Si `requires_secondary_app == True`: Valida `secondary_app_actions` y determina aplicación secundaria
       - Retorna: `(is_valid: bool, errors: List[str], execution_params: dict)`
     - **Si `is_valid == False`**:
       - NO continuar con ejecución de acciones (saltar pasos 7.2 y 7.3)
       - Actualizar `SOLUCION` con mensaje de error claro:
         - "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación. Por favor, contacte al soporte."
       - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de error
       - Establecer `CODUSOLUCION = "AGENTE-MS"`
       - Agregar información en `AI_CLASSIFICATION_DATA`:
         ```python
         {
             "validation_failed": True,
             "validation_errors": errors,  # Lista de errores de validación
             "validation_timestamp": datetime.utcnow().isoformat(),
             "processing_status": "validation_failed",
             "current_step": "Validación de requisitos falló",
             "progress_percentage": 45,
             "error_details": {
                 "error_type": "classification_validation_failed",
                 "user_message": "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación.",
                 "action_suggestion": "Por favor, contacte al soporte para asistencia."
             }
         }
         ```
       - Registrar errores en logs con severidad ERROR:
         ```python
         logger.error(
             "Validación de requisitos de clasificación falló",
             codpeticiones=codpeticiones,
             app_type=app_type,
             errors=errors,
             classification_result=classification_result.model_dump()
         )
         ```
       - Retornar inmediatamente (NO ejecutar acciones, NO continuar con procesamiento)
     - **Si `is_valid == True`**:
       - Guardar `execution_params` para uso en Paso 7.3 (Ejecución de Acciones)
       - `execution_params` contiene:
         - Para una sola aplicación: `{"mapped_actions": [...], "user_id": "...", "user_name": "..." (si aplica)}`
         - Para múltiples aplicaciones: `{"primary_app": "...", "primary_actions": [...], "requires_secondary_app": True, "secondary_app": "...", "secondary_app_actions": [...], "user_id": "...", "user_name": "..." (si aplica)}`
       - Continuar con procesamiento normal (ir al paso 7.2)
   
   - **Paso 7.2: Validación y Extracción** (actualizar progreso al 50%):
     - Actualizar `SOLUCION`: "Validando información y preparando acciones necesarias..."
     - Actualizar `AI_CLASSIFICATION_DATA.processing_status = "validating"`
     - Actualizar `AI_CLASSIFICATION_DATA.progress_percentage = 50`
     - Validar categoría con `AIProcessor.validate_category()`
     - Extraer parámetros con `AIProcessor.extract_parameters()` (preferir `extracted_params` del `ClassificationResult`, ya procesado por Gemini)
   
   - **Paso 7.3: Ejecución de Acciones** (actualizar progreso al 70%):
     - **IMPORTANTE**: Usar `execution_params` validados en el Paso 7.1.6 (NO construir parámetros desde cero)
     - **Determinar aplicaciones a procesar**:
       - Si `execution_params.requires_secondary_app == True`:
         - Procesar ambas aplicaciones secuencialmente
         - Aplicación principal primero, luego aplicación secundaria
       - Si `execution_params.requires_secondary_app == False`:
         - Procesar solo aplicación principal
     - **Para Dominio (principal o secundario)**: SIEMPRE ejecutar `find_user` PRIMERO antes de cualquier otra acción:
       - Actualizar `SOLUCION`: "Buscando información del usuario en el sistema..."
       - Actualizar `AI_CLASSIFICATION_DATA.processing_status = "executing_actions"`
       - Actualizar `AI_CLASSIFICATION_DATA.progress_percentage = 70`
       - Ejecutar `ActionExecutor.execute_dominio_action()` con `action_type="find_user"`:
         - Usar `user_name` de `execution_params` (ya validado en Paso 7.1.6)
         - Usar `user_id` de `execution_params` (ya validado en Paso 7.1.6)
       - Si `find_user` retorna `found: false`:
         - Actualizar `SOLUCION` con mensaje: "No se encontró el usuario especificado en el sistema. Por favor, verifique el nombre de usuario o contacte al soporte para aclaración."
         - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de aclaración
         - Establecer `CODUSOLUCION = "AGENTE-MS"`
         - Agregar información en `AI_CLASSIFICATION_DATA`:
           ```python
           {
               "actions_executed": [{
                   "action_type": "find_user",
                   "success": False,
                   "result": {"found": False},
                   "timestamp": datetime.utcnow().isoformat()
               }],
               "error_details": {
                   "error_type": "user_not_found",
                   "user_message": "No se encontró el usuario especificado en el sistema. Por favor, verifique el nombre de usuario o contacte al soporte para aclaración.",
                   "action_suggestion": "Verifique que el nombre de usuario sea correcto o contacte al soporte para asistencia."
               }
           }
           ```
         - NO continuar con acciones siguientes (`change_password` o `unlock_account`)
         - Retornar (terminar procesamiento)
       - Si `find_user` retorna `found: true`:
         - Usar `user_id` del resultado para acciones siguientes
         - Continuar con ejecución de `change_password` o `unlock_account` según `detected_actions`
     
     - **Para Amerika (principal o secundario)**: No requiere `find_user`, ejecutar directamente las acciones detectadas
     
     - **Ejecutar acciones en orden secuencial para cada aplicación**:
       - **PASO 1: Procesar aplicación principal**:
         - **IMPORTANTE**: Usar `execution_params.primary_actions` o `execution_params.mapped_actions` (según estructura)
         - Para cada acción en las acciones principales (después de `find_user` si aplica):
           - Ejecutar acción con `ActionExecutor` según `app_type` principal
           - Registrar resultado en `actions_executed`
       - **PASO 2: Procesar aplicación secundaria (si aplica)**:
         - Solo si `execution_params.requires_secondary_app == True`
         - **IMPORTANTE**: Usar `execution_params.secondary_app_actions` (ya mapeadas si es Amerika)
         - Para cada acción en `execution_params.secondary_app_actions`:
           - Ejecutar acción con `ActionExecutor` según `execution_params.secondary_app`
           - Registrar resultado en `actions_executed`
       - **Estrategia de continuación**: Si una acción falla, continuar con las siguientes acciones (no detener el procesamiento)
       - Para cada acción en `execution_params.mapped_actions` o `execution_params.primary_actions` (después de `find_user` si aplica):
         - Actualizar `SOLUCION` con mensaje específico según la acción:
           - Para Amerika: `generate_password`: "Generando nueva contraseña para su cuenta..."
           - Para Dominio: `change_password`: "Generando nueva contraseña para su cuenta..."
           - `unlock_account`: "Desbloqueando su cuenta..."
         - Ejecutar acción con `ActionExecutor`:
           - Para Amerika: Usar `execution_params.user_id` y `execution_params.mapped_actions`
           - Para Dominio: Usar `execution_params.user_id`, `execution_params.user_name` y `execution_params.mapped_actions`
         - Si la acción falla:
           - Registrar error en `actions_executed` pero CONTINUAR con siguiente acción (no detener)
           - Actualizar con mensaje amigable (ver FASE 2.5)
         - Incrementar progreso según número de acciones (70% + (número_accion / total_acciones * 20%))
       - Al final, si alguna acción falló:
         - Generar mensaje combinado: éxito + errores (ver FASE 5.3 para detalles)
         - Actualizar `SOLUCION` con detalles de acciones exitosas y fallidas
   
   - **Paso 7.4: Finalización** (actualizar progreso al 100%):
     - Generar mensaje final de solución (ver FASE 5.4, punto 5: Generar mensaje de solución final)
     - Actualizar `CODESTADO = 3` (SOLUCIONADO)
     - Actualizar `SOLUCION` con mensaje final completo
     - Actualizar `AI_CLASSIFICATION_DATA.processing_status = "completed"`
     - Actualizar `AI_CLASSIFICATION_DATA.progress_percentage = 100`
     - Actualizar solicitud en Supabase (ver siguiente fase)

7. **Manejar errores durante procesamiento con try-catch completo**:
   - **Envolver TODO el procesamiento en try-catch**:
     ```python
     async def process_new_request(self, request_data: dict):
         codpeticiones = request_data.get("CODPETICIONES")
         
         try:
             # Paso 1: Validación inicial
             # ... validaciones ...
             
             # Paso 2: Clasificación con IA
             # ... clasificación ...
             
             # Paso 3: Ejecución de acciones
             # ... ejecución ...
             
             # Paso 4: Actualización final
             # ... actualización ...
             
         except ValidationError as e:
             # Error de validación: Actualizar solicitud con mensaje de rechazo
             logger.warning("Solicitud rechazada por validación", codpeticiones=codpeticiones, error=str(e))
             await self._update_request_with_rejection(codpeticiones, str(e))
             return
         
         except RateLimitExceededError as e:
             # Rate limit excedido: Actualizar solicitud con mensaje de rechazo
             logger.warning("Solicitud rechazada por rate limit", codpeticiones=codpeticiones, user=e.user_id)
             await self._update_request_with_rejection(codpeticiones, e.message)
             return
         
         except AIClassificationError as e:
             # Error en clasificación: Usar fallback y continuar
             logger.error("Error en clasificación, usando fallback", codpeticiones=codpeticiones, error=str(e))
             classification_result = self._get_fallback_classification(...)
             # Continuar con procesamiento usando fallback
         
         except ActionExecutionError as e:
             # Error en ejecución de acción: Actualizar solicitud con mensaje amigable
             logger.error("Error al ejecutar acción", codpeticiones=codpeticiones, error=str(e))
             await self._update_request_with_error(
                 codpeticiones,
                 user_message=e.user_message,
                 action_suggestion=e.action_suggestion
             )
             return
         
         except SupabaseConnectionError as e:
             # Error de conexión con Supabase: Reintentar actualización
             logger.error("Error de conexión con Supabase", codpeticiones=codpeticiones, error=str(e))
             await self._add_to_retry_queue(codpeticiones, updates)
             # NO lanzar excepción para no detener procesamiento de otras solicitudes
             return
         
         except Exception as e:
             # Cualquier otro error inesperado
             logger.error(
                 "Error inesperado al procesar solicitud",
                 codpeticiones=codpeticiones,
                 error=str(e),
                 exc_info=True
             )
             # Actualizar solicitud con mensaje genérico amigable
             await self._update_request_with_error(
                 codpeticiones,
                 user_message="Ocurrió un error inesperado al procesar tu solicitud. Nuestro equipo ha sido notificado.",
                 action_suggestion="Tu solicitud será reintentada automáticamente. Si el problema persiste, contacta al soporte."
             )
             # NO lanzar excepción para no detener procesamiento de otras solicitudes
             return
     ```
   - **Casos edge específicos a manejar**:
     - **¿Qué pasa si Gemini API falla completamente?**
       - Usar fallback de clasificación basada en categoría
       - Continuar procesamiento con valores por defecto seguros
       - Actualizar solicitud con mensaje informativo
     - **¿Qué pasa si el backend FastAPI está caído?**
       - Capturar `BackendConnectionError`
       - Actualizar solicitud con mensaje amigable
       - Agregar a cola de reintentos para procesamiento posterior
     - **¿Qué pasa si Supabase está caído?**
       - Capturar `SupabaseConnectionError`
       - Mantener actualizaciones en cola local
       - Reintentar cuando Supabase se recupere
     - **¿Qué pasa si hay un timeout en cualquier operación?**
       - Capturar `TimeoutError` o `asyncio.TimeoutError`
       - Reintentar con timeout mayor
       - Si falla definitivamente, usar fallback o agregar a cola de reintentos
     - **¿Qué pasa si hay un error de validación de datos?**
       - Capturar `ValidationError`
       - Actualizar solicitud con mensaje de rechazo claro
       - NO procesar la solicitud
   - **No bloquear procesamiento de otras solicitudes**:
     - Cada solicitud se procesa de forma independiente
     - Un error en una solicitud NO debe detener el listener
     - Registrar todos los errores en logs para debugging

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/realtime_listener.py`

### 5.4. Actualización de Solicitudes en Supabase con Feedback Progresivo

**Objetivo**: Actualizar solicitudes con resultados del procesamiento y proporcionar feedback progresivo al usuario durante todo el proceso.

**Tareas**:
1. Implementar método `update_request()`:
   - Parámetros: `codpeticiones: int`, `updates: dict`
   - Usar cliente de Supabase para actualizar:
     ```python
     supabase.table("HLP_PETICIONES").update(updates).eq("CODPETICIONES", codpeticiones).execute()
     ```

2. Implementar método `update_request_progress()` para feedback progresivo:
   - Parámetros: `codpeticiones: int`, `status: str`, `message: str`, `progress: int`, `metadata: Optional[dict] = None`
   - Actualizar `SOLUCION` con mensaje informativo (temporal, será reemplazado por mensaje final)
   - Actualizar `AI_CLASSIFICATION_DATA` con información de progreso (ver subsección 5.4.1 para estructura completa)
   - Mantener `CODESTADO = 2` (TRAMITE) durante el procesamiento
   - Solo cambiar a `CODESTADO = 3` (SOLUCIONADO) cuando se complete o falle definitivamente
   - **IMPORTANTE**: Si se corrigió la categoría (Paso 7.1.5), `CODCATEGORIA` ya debe estar actualizado en Supabase antes de continuar con el procesamiento

### 5.4.1. Estructura Completa de AI_CLASSIFICATION_DATA

**Objetivo**: Definir la estructura fija y completa del campo `AI_CLASSIFICATION_DATA` que se utilizará durante todo el procesamiento de la solicitud.

**Importante**: Esta estructura se define desde el inicio y cada actualización REEMPLAZA el objeto completo (no se hace merge incremental). Todos los campos deben estar presentes desde la primera actualización, usando `null` para campos que aún no se han llenado.

**Estructura Completa**:
```python
{
    # Datos de clasificación (se llenan en paso 7.1 de FASE 5.3)
    "app_type": "amerika" | "dominio" | null,
    "confidence": 0.0-1.0 | null,
    "detected_actions": List[str] | null,
    "reasoning": str | null,
    "extracted_params": dict | null,
    "requires_secondary_app": bool | null,  # True si también se requiere la otra aplicación
    "secondary_app_actions": List[str] | null,  # Acciones para aplicación secundaria
    "original_codcategoria": int | null,  # Categoría original seleccionada por el usuario (para auditoría)
    "corrected_codcategoria": int | null,  # Categoría corregida (si hubo discrepancia)
    "category_corrected": bool | null,  # True si se corrigió la categoría
    "raw_classification": str | null,
    "classification_timestamp": str ISO8601 | null,
    
    # Estado de procesamiento (se actualiza en cada paso)
    "processing_status": "validated" | "classifying" | "validating" | "executing_actions" | "completed" | "error" | "ignored",
    "current_step": str,
    "progress_percentage": int (0-100),
    "last_update": str ISO8601,
    
    # Resultados de acciones (se llenan en paso 7.3 de FASE 5.3)
    "actions_executed": List[dict] | null,  # [{app_type: str, action_type: str, success: bool, result: dict, timestamp: str ISO8601}]
    # Nota: Cada acción debe incluir "app_type" para identificar si es de aplicación principal o secundaria
    
    # Información de finalización
    "completed_at": str ISO8601 | null,
    "fallback_used": bool | null,
    "error_details": dict | null,  # Solo si hay error: {error_type: str, user_message: str, action_suggestion: str, technical_detail: str}
    
    # Información de ignorado (solo si codcategoria no es 300 ni 400)
    "ignored": bool | null,
    "ignore_reason": str | null,
    "requires_human_review": bool | null,
    "auto_processing_skipped": bool | null,
    "ignored_at": str ISO8601 | null
}
```

**Reglas de Actualización**:
- Cada actualización debe incluir TODOS los campos de la estructura
- Campos que aún no se han llenado deben ser `null`
- Campos que ya se llenaron deben mantener sus valores (no se pierden en actualizaciones posteriores)
- El objeto completo se reemplaza en cada actualización, pero los valores existentes se preservan

**Ejemplo de Actualización Inicial (después de validación)**:
```python
{
    "app_type": null,
    "confidence": null,
    "detected_actions": null,
    "reasoning": null,
    "extracted_params": null,
    "requires_secondary_app": null,
    "secondary_app_actions": null,
    "original_codcategoria": 300,  # Categoría original seleccionada por el usuario
    "corrected_codcategoria": null,  # Se actualizará si hay discrepancia
    "category_corrected": false,  # Se actualizará si hay discrepancia
    "raw_classification": null,
    "classification_timestamp": null,
    "processing_status": "validated",
    "current_step": "Clasificando solicitud con inteligencia artificial...",
    "progress_percentage": 10,
    "last_update": "2024-01-15T10:30:00Z",
    "actions_executed": null,
    "completed_at": null,
    "fallback_used": null,
    "error_details": null,
    "ignored": null,
    "ignore_reason": null,
    "requires_human_review": null,
    "auto_processing_skipped": null,
    "ignored_at": null
}
```

**Ejemplo de Actualización Final (solicitud completada con corrección de categoría)**:
```python
{
    "app_type": "amerika",
    "confidence": 0.85,
    "detected_actions": ["change_password"],
    "reasoning": "Usuario menciona explícitamente 'Amerika' pero seleccionó categoría 300 (dominio). Se detecta necesidad real: Amerika. El sistema corregirá automáticamente la categoría de 300 a 400.",
    "extracted_params": {"user_id": "mzuloaga"},
    "requires_secondary_app": false,
    "secondary_app_actions": null,
    "original_codcategoria": 300,  # Categoría original seleccionada por el usuario
    "corrected_codcategoria": 400,  # Categoría corregida automáticamente
    "category_corrected": true,  # Indica que se corrigió la categoría
    "raw_classification": "{...}",
    "classification_timestamp": "2024-01-15T10:30:15Z",
    "processing_status": "completed",
    "current_step": "Solicitud procesada exitosamente. Categoría corregida automáticamente.",
    "progress_percentage": 100,
    "last_update": "2024-01-15T10:30:45Z",
    "actions_executed": [
        {
            "app_type": "principal",
            "action_type": "generate_password",
            "success": true,
            "result": {"password_length": 15, "generated_at": "2024-01-15T10:30:30Z"},
            "timestamp": "2024-01-15T10:30:30Z"
        }
    ],
    "completed_at": "2024-01-15T10:30:45Z",
    "fallback_used": false,
    "error_details": null,
    "ignored": false,
    "ignore_reason": null,
    "requires_human_review": false,
    "auto_processing_skipped": false,
    "ignored_at": null
}
```

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/realtime_listener.py` (usar esta estructura en todos los métodos de actualización)

3. Estructura de `updates` para solicitud resuelta (final):
   - Usar la estructura completa de `AI_CLASSIFICATION_DATA` definida en subsección 5.4.1
   - Todos los campos deben estar presentes (usar `null` para campos no aplicables)
   - **IMPORTANTE**: Si se corrigió la categoría, `CODCATEGORIA` ya debe estar actualizado (se actualizó en Paso 7.1.5)
   - Ejemplo:
   ```python
   {
       "CODESTADO": 3,  # SOLUCIONADO
       "SOLUCION": solucion_text,  # Mensaje formal final al usuario
       "FESOLUCION": datetime.utcnow().isoformat(),
       "CODUSOLUCION": "AGENTE-MS",
       "FECCIERRE": datetime.utcnow().isoformat(),
       "CODMOTCIERRE": 5,  # Respuesta Final
       # CODCATEGORIA ya está actualizado si hubo corrección (Paso 7.1.5)
       "AI_CLASSIFICATION_DATA": {
           # Estructura completa según subsección 5.4.1
           "app_type": "amerika",
           "confidence": 0.95,
           "detected_actions": ["change_password"],
           "reasoning": "...",
           "extracted_params": {...},
           "original_codcategoria": 300,  # Categoría original (si hubo corrección)
           "corrected_codcategoria": 400,  # Categoría corregida (si hubo corrección)
           "category_corrected": True,  # True si se corrigió
           "raw_classification": "...",
           "classification_timestamp": "...",
           "processing_status": "completed",
           "current_step": "Solicitud procesada exitosamente",
           "progress_percentage": 100,
           "last_update": "...",
           "actions_executed": [...],
           "completed_at": "...",
           "fallback_used": false,
           "error_details": null,
           "ignored": false,
           "ignore_reason": null,
           "requires_human_review": false,
           "auto_processing_skipped": false,
           "ignored_at": null
       }
   }
   ```

4. Estructura de `updates` para solicitud en trámite (progreso intermedio):
   - Usar la estructura completa de `AI_CLASSIFICATION_DATA` definida en subsección 5.4.1
   - Campos que aún no se han llenado deben ser `null`
   - Ejemplo:
   ```python
   {
       "CODESTADO": 2,  # TRAMITE
       "SOLUCION": "Mensaje informativo del paso actual...",  # Feedback temporal
       "AI_CLASSIFICATION_DATA": {
           # Estructura completa según subsección 5.4.1
           "app_type": null,  # Aún no clasificado
           "confidence": null,
           "detected_actions": null,
           "reasoning": null,
           "extracted_params": null,
           "raw_classification": null,
           "classification_timestamp": null,
           "processing_status": "classifying",
           "current_step": "Analizando su solicitud con inteligencia artificial...",
           "progress_percentage": 30,
           "last_update": datetime.utcnow().isoformat(),
           "actions_executed": null,
           "completed_at": null,
           "fallback_used": null,
           "error_details": null,
           "ignored": null,
           "ignore_reason": null,
           "requires_human_review": null,
           "auto_processing_skipped": null,
           "ignored_at": null
       }
   }
   ```

4. **Mensajes de Feedback Progresivo** (usar durante procesamiento):
   - **Validación Inicial** (10%):
     - "Su solicitud está siendo procesada. El sistema está analizando su solicitud..."
   - **Clasificación con IA** (30%):
     - "Analizando su solicitud con inteligencia artificial para determinar el tipo de aplicación y acciones necesarias..."
   - **Validación y Preparación** (50%):
     - "Validando información y preparando acciones necesarias..."
   - **Ejecución de Acciones** (70-90%):
     - Para `change_password`: "Generando nueva contraseña para su cuenta..."
     - Para `unlock_account`: "Desbloqueando su cuenta..."
     - Para `find_user`: "Buscando información del usuario en el sistema..."
     - Para múltiples acciones: "Ejecutando acciones necesarias: [lista de acciones]..."
   - **Finalización** (100%):
     - Generar mensaje final completo (ver siguiente punto)

5. **Generar mensaje de solución final (`SOLUCION`)**:
   - **Nota sobre Generación de Mensajes**: Los mensajes finales se generan mediante **lógica programática (plantillas predefinidas)**, no con IA adicional. Esto reduce costos (no requiere llamadas adicionales a Gemini) y garantiza consistencia en la comunicación con el usuario.
   - **Si se procesaron múltiples aplicaciones (`requires_secondary_app == True`)**:
     - Generar mensaje combinado que cubra ambas aplicaciones
     - Estructura: "Se procesaron sus solicitudes en ambas aplicaciones:\n\n**{APP_PRINCIPAL}**: [mensajes de acciones principales]\n\n**{APP_SECUNDARIA}**: [mensajes de acciones secundarias]"
     - Incluir contraseñas generadas de ambas aplicaciones si aplica
     - Incluir resultados de desbloqueo de ambas aplicaciones si aplica
     - Ejemplo: "Se procesaron sus solicitudes en ambas aplicaciones:\n\n**DOMINIO**: Se ha generado una nueva contraseña: {password_dominio}\n\n**AMERIKA**: Su cuenta ha sido desbloqueada exitosamente."
   - **Si se procesó una sola aplicación**:
     - Si acción fue `change_password`:
       - Incluir contraseña generada (si aplica)
       - Mensaje formal: "Se ha generado una nueva contraseña para su cuenta de {app_type}. Su nueva contraseña es: {password}. Por favor, guárdela en un lugar seguro y cámbiela después de iniciar sesión."
     - Si acción fue `unlock_account`:
       - Mensaje formal: "Su cuenta de {app_type} ha sido desbloqueada exitosamente. Ya puede iniciar sesión normalmente."
     - Si ambas acciones:
       - Combinar mensajes apropiadamente: "Se ha generado una nueva contraseña para su cuenta de {app_type}: {password}. Además, su cuenta ha sido desbloqueada exitosamente. Ya puede iniciar sesión con su nueva contraseña."
   - **Si hubo errores**:
     - Usar mensaje amigable del backend (ver FASE 2.5: Manejo de Errores HTTP del Backend con Mensajes Amigables)
     - Incluir información sobre reintentos automáticos si aplica
     - Si algunas acciones fueron exitosas y otras fallaron, combinar mensajes: éxito primero, luego errores
   - Formato profesional y claro para el usuario final
   - **IMPORTANTE**: El mensaje final reemplaza todos los mensajes de progreso anteriores

5. Manejar errores de actualización:
   - `UpdateError`: Error al actualizar en Supabase
   - Retry con backoff exponencial
   - Registrar error en logs si falla definitivamente

6. **Nota sobre Feedback Progresivo**:
   - **IMPORTANTE**: Cada actualización de progreso debe ser visible para el usuario en tiempo real
   - Usar `update_request_progress()` para actualizaciones intermedias (no solo al final)
   - El frontend mostrará automáticamente el progreso gracias a Supabase Realtime
   - Los mensajes en `SOLUCION` durante el procesamiento son temporales y serán reemplazados por el mensaje final
   - Mantener `CODESTADO = 2` (TRAMITE) durante todo el procesamiento, solo cambiar a `CODESTADO = 3` (SOLUCIONADO) al finalizar

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/services/realtime_listener.py`

---

## FASE 6: Punto de Entrada y Orquestación (main.py)

**Justificación**: Implementar el punto de entrada principal que orquesta todos los componentes.

### 6.1. Estructura del Punto de Entrada

**Objetivo**: Crear el punto de entrada principal que inicializa y orquesta todos los servicios.

**Tareas**:
1. Crear función `main()` en `agent/main.py`:
   - Cargar configuración usando `get_settings()`
   - Configurar logging estructurado con `structlog`
   - Inicializar servicios:
     - `ActionExecutor(settings)`
     - `AIProcessor(settings)`
     - `RequestValidator(settings)` (nuevo)
     - `RealtimeListener(settings, action_executor, ai_processor, request_validator)`

2. Implementar manejo de señales (SIGINT, SIGTERM):
   - Capturar señales para shutdown graceful
   - Cerrar conexiones y recursos apropiadamente
   - Registrar evento de shutdown en logs

3. Iniciar listener de Realtime con validación:
   - Llamar a `realtime_listener.subscribe_to_new_requests()`
   - **Validar que la suscripción se estableció correctamente**:
     ```python
     subscription = await realtime_listener.subscribe_to_new_requests()
     
     if subscription:
         logger.info(
             "✅ Agente AI iniciado correctamente",
             listener_status="ACTIVO",
             supabase_realtime="CONECTADO",
             ready_to_process_requests=True
         )
         # Log de consola para validación visible
         print("\n✅ Agente AI está ESCUCHANDO eventos de creación de solicitudes")
         print("   Esperando nuevas solicitudes en tabla HLP_PETICIONES...\n")
     else:
         logger.error("❌ No se pudo establecer suscripción a eventos Realtime")
         print("\n❌ ERROR: No se pudo establecer suscripción a eventos Realtime")
         raise SupabaseConnectionError("No se pudo establecer suscripción a eventos Realtime")
     ```
   - Mantener el proceso corriendo (loop infinito o asyncio.run())

4. Manejar excepciones no capturadas:
   - Capturar todas las excepciones en el nivel superior
   - Registrar en logs con contexto completo
   - No terminar el proceso a menos que sea crítico

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/main.py`

### 6.2. Logging Estructurado

**Objetivo**: Configurar logging estructurado para facilitar debugging y monitoreo.

**Tareas**:
1. Configurar `structlog` en `main.py`:
   - Configurar procesadores de structlog
   - Configurar formato JSON para producción
   - Configurar formato legible para desarrollo

2. Crear logger por módulo:
   - Cada servicio debe tener su propio logger
   - Usar nombres descriptivos: `agent.services.action_executor`, etc.

3. Registrar eventos importantes:
   - Inicio/fin de procesamiento de solicitud
   - Clasificación de IA (con confianza)
   - Ejecución de acciones (con resultados)
   - Actualización de solicitudes
   - Errores y excepciones (con stack trace)

4. Incluir contexto relevante en logs:
   - `codpeticiones`: ID de solicitud
   - `user_id`: ID de usuario
   - `action_type`: Tipo de acción
   - `app_type`: Tipo de aplicación detectada
   - `confidence`: Confianza de clasificación

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/main.py`
- Todos los archivos de servicios (agregar logging)

### 6.3. Manejo de Errores Global

**Objetivo**: Implementar manejo robusto de errores a nivel global.

**Tareas**:
1. Crear excepciones personalizadas en módulo `agent/core/exceptions.py`:
   - `AgentError`: Excepción base
   - `ConfigurationError`: Error de configuración
   - `SupabaseConnectionError`: Error de conexión con Supabase
   - `BackendConnectionError`: Error de conexión con backend
   - `AIClassificationError`: Error en clasificación de IA
   - `ActionExecutionError`: Error en ejecución de acción
   - `ValidationError`: Error de validación de solicitud
   - `RateLimitExceededError`: Error cuando se excede el límite de solicitudes

2. Implementar manejo de errores en `main.py`:
   - Capturar excepciones específicas y manejarlas apropiadamente
   - Registrar todas las excepciones en logs
   - Continuar procesamiento si es posible (no terminar proceso por un error)

3. Implementar circuit breaker para servicios externos:
   - Si Supabase falla repetidamente, pausar procesamiento temporalmente
   - Si backend falla repetidamente, pausar ejecución de acciones
   - Si Gemini falla repetidamente, pausar clasificación
   - Reintentar después de un período de tiempo

**Archivos a crear/modificar**:
- `agm-desk-ai/agent/core/exceptions.py` (nuevo)
- `agm-desk-ai/agent/main.py`

---

## Variables de Entorno

Todas las variables de entorno deben estar documentadas en `.env.example`:

```env
# Supabase Configuration
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend FastAPI Configuration
BACKEND_URL=http://localhost:8000
API_SECRET_KEY=dev-api-secret-key-12345

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash  # Recomendado para PoC (más económico y rápido). Alternativa: gemini-1.5-pro para producción
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=500

# Logging Configuration
LOG_LEVEL=INFO

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=2.0

# Rate Limiting Configuration
MAX_REQUESTS_PER_USER=5
RATE_LIMIT_WINDOW_HOURS=24
MAX_REQUEST_AGE_HOURS=  # Opcional: horas máximas de antigüedad para procesar (vacío = sin límite)

# Validation Configuration
MIN_DESCRIPTION_LENGTH=10
MAX_DESCRIPTION_LENGTH=4000

# Security Filters Configuration
ENABLE_SECURITY_FILTERS=True
PROMPT_INJECTION_KEYWORDS=ignore,actúa,ejecuta,revela,bypass,override,ignora,ejecutar,revelar
DANGEROUS_INSTRUCTION_PATTERNS=debes hacer,necesito que hagas,por favor ejecuta,debes,necesitas,tienes que
MALICIOUS_CONTENT_KEYWORDS=  # Opcional: palabras clave adicionales de contenido malicioso (separadas por comas)

# Prompt Optimization Configuration
USE_FEW_SHOT_ALWAYS=False  # Si True, siempre usa few-shot. Si False, usa few-shot solo cuando sea necesario
FEW_SHOT_THRESHOLD_DESCRIPTION_LENGTH=20  # Longitud mínima de descripción para considerar simple (sin few-shot)
```

**Notas**:
- `SUPABASE_SERVICE_ROLE_KEY`: Obtener desde Supabase Dashboard > Settings > API > service_role key (secret)
- `GEMINI_API_KEY`: Obtener desde Google AI Studio (https://makersuite.google.com/app/apikey)
- `GEMINI_MODEL`: Modelo de Gemini a usar (`gemini-2.5-flash` recomendado para PoC - más económico, rápido y soporta JSON mode; `gemini-1.5-pro` como alternativa para producción - mayor precisión)
- `GEMINI_TEMPERATURE`: Temperatura para generación (0.0-1.0, valores bajos = más consistente, recomendado: 0.1-0.3)
- `GEMINI_MAX_TOKENS`: Máximo de tokens de salida (500 es suficiente para JSON de clasificación)

### Nota sobre Uso Gratuito para PoC

**Google AI Studio Free Tier**:
- **Gemini 2.5 Flash está disponible en el nivel gratuito de Google AI Studio**
- El free-tier incluye cuotas generosas suficientes para desarrollo y pruebas de PoC
- Para la fase de simulación y ejercicios académicos, el uso gratuito será suficiente
- **Obtener API Key gratuita**: https://makersuite.google.com/app/apikey
- **Nota importante**: Cualquier uso intensivo o en producción requerirá migrar al plan de pago
- Las cuotas gratuitas pueden variar según la política de Google, verificar límites actuales en la documentación oficial
- `BACKEND_URL`: URL del backend FastAPI (puede ser localhost para desarrollo o URL de producción)
- `API_SECRET_KEY`: Debe coincidir con `API_SECRET_KEY` configurada en el backend
- `MAX_REQUESTS_PER_USER`: Número máximo de solicitudes que un usuario puede crear en la ventana de tiempo
- `RATE_LIMIT_WINDOW_HOURS`: Ventana de tiempo deslizante en horas para contar solicitudes (ej: 24 = últimas 24 horas)
- `MAX_REQUEST_AGE_HOURS`: (Opcional) Si está configurado, rechaza solicitudes más antiguas que este valor. Dejar vacío para no aplicar límite de edad.
- `MIN_DESCRIPTION_LENGTH` / `MAX_DESCRIPTION_LENGTH`: Límites de longitud para la descripción de la solicitud
- `ENABLE_SECURITY_FILTERS`: Habilitar/deshabilitar filtros de seguridad (default: True). Solo deshabilitar para debugging.
- `PROMPT_INJECTION_KEYWORDS`: Palabras clave para detectar intentos de prompt injection (separadas por comas)
- `DANGEROUS_INSTRUCTION_PATTERNS`: Patrones para detectar instrucciones peligrosas al asistente (separados por comas)
- `MALICIOUS_CONTENT_KEYWORDS`: (Opcional) Palabras clave adicionales de contenido malicioso (separadas por comas)
- `USE_FEW_SHOT_ALWAYS`: Si True, siempre usa few-shot examples. Si False, usa few-shot solo cuando se detecte complejidad (default: False)
- `FEW_SHOT_THRESHOLD_DESCRIPTION_LENGTH`: Longitud mínima de descripción para considerar simple (sin few-shot) (default: 20)

---

## Flujo de Procesamiento Completo

### 1. Detección de Nueva Solicitud
- **Validación de Escucha (CRÍTICO - Primer Paso)**:
  - Al iniciar, el agente valida que puede escuchar eventos de Supabase Realtime
  - Log de consola visible: "🔔 AGENTE AI - LISTENER ACTIVO" con detalles de configuración
  - Log estructurado: "✅ Suscripción a eventos Realtime establecida exitosamente"
- **Recepción de Evento**:
  - RealtimeListener detecta evento INSERT en `HLP_PETICIONES`
  - **Log inmediato de validación**: "🎯 EVENTO RECIBIDO - Nueva solicitud detectada" (visible en consola)
  - Log de consola: "[EVENTO RECIBIDO] Solicitud #X detectada" con timestamp
  - Verifica que `CODESTADO = 1` (PENDIENTE)
  - Extrae datos de la solicitud del payload

### 2. Validación y Sanitización de Entrada
- **Validación de Estructura**: Verificar que todos los campos requeridos estén presentes y tengan tipos correctos
- **Sanitización de Descripción**: Limpiar espacios, normalizar, validar longitud y caracteres
- **Validación de Categoría**: Verificar que la categoría sea válida (300 o 400) y exista en BD
- **Validación de Usuario**: Verificar formato y validez del `ususolicita`
- Si alguna validación falla: Actualizar solicitud con mensaje de error y terminar procesamiento

### 3. Validación de Seguridad (CRÍTICO)
- **Filtros de Seguridad para IA**: Ejecutar filtros de seguridad ANTES de enviar a Gemini AI:
  - Detectar intentos de prompt injection
  - Detectar instrucciones peligrosas al asistente
  - Escanear contenido malicioso (SQL injection, XSS, command injection, etc.)
- Si se detecta riesgo ALTO o CRÍTICO:
  - NO enviar a Gemini AI (prevenir prompt injection)
  - Rechazar la solicitud inmediatamente
  - Actualizar solicitud con mensaje de rechazo profesional
  - Registrar en logs con severidad ALTA/CRÍTICA para auditoría
  - Terminar procesamiento (no continuar con clasificación)
- Si se detecta riesgo MEDIO:
  - Registrar warning en logs
  - Continuar procesamiento con precaución
  - Agregar flag de advertencia en metadata

### 4. Validación de Rate Limiting
- Consultar número de solicitudes del usuario en la ventana de tiempo configurada
- Comparar con `MAX_REQUESTS_PER_USER`
- Si excede el límite:
  - Generar mensaje de rechazo claro y profesional
  - Actualizar solicitud con mensaje de rechazo
  - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de rechazo
  - Registrar evento en logs para auditoría
  - Terminar procesamiento (no procesar la solicitud)

### 5. Validación de Edad de Solicitud
- Calcular edad de la solicitud desde `FESOLICITA`
- Si `MAX_REQUEST_AGE_HOURS` está configurado y la solicitud es más antigua:
  - Generar mensaje de rechazo
  - Actualizar solicitud con mensaje de rechazo
  - Terminar procesamiento

### 6. Actualización a Estado TRAMITE
- Si todas las validaciones pasan, actualizar `CODESTADO = 2` (TRAMITE)
- Esto indica que la solicitud está siendo procesada activamente

### 7. Clasificación con IA (Optimizada)
- AIProcessor recibe `description`, `codcategoria`, `ususolicita`
- **Optimización de System Prompt**:
  - **PASO 1**: Determinar complejidad con `_should_use_few_shot_examples()`
  - **PASO 2**: Seleccionar System Prompt apropiado:
    - Si solicitud es compleja → Usar `CLASSIFICATION_SYSTEM_PROMPT_WITH_EXAMPLES` (~800-1000 tokens)
    - Si solicitud es simple → Usar `CLASSIFICATION_SYSTEM_PROMPT_BASE` (~400-500 tokens)
  - **Ahorro estimado**: ~40-50% de tokens en casos típicos (80% simples, 20% complejos)
- Construye prompt optimizado:
  - System Prompt: Seleccionado según complejidad, cargado una vez al inicio, reutilizado
  - User Message: Solo descripción y categoría (mínimo contexto)
- Llamar a Gemini AI con configuración optimizada:
  - `response_mime_type="application/json"` (si está disponible)
  - `temperature`: 0.2 (bajo para consistencia)
  - `max_output_tokens`: 500 (suficiente para JSON)
- Obtiene clasificación en formato JSON estructurado:
  - `app_type`: "amerika" o "dominio" (aplicación principal)
  - `confidence`: Nivel de confianza
  - `detected_actions`: Lista de acciones a ejecutar para aplicación principal
  - `requires_secondary_app`: bool (True si también se requiere la otra aplicación)
  - `secondary_app_actions`: Lista de acciones para aplicación secundaria (si aplica)
  - `extracted_params`: Parámetros extraídos (ya procesados, no requiere llamada adicional)
- Validar respuesta con Pydantic `ClassificationResult` (garantiza estructura correcta)

### 8. Detección y Corrección de Categoría
- **OBJETIVO**: Detectar discrepancia entre `codcategoria` seleccionada por el usuario y `app_type` detectado por la IA, y corregir la categoría automáticamente.
- **IMPORTANTE**: La categoría es importante y debe ser correcta. Si el usuario la selecciona mal, el agente debe corregirla.
- **Mapeo de categorías**:
  - `app_type == "dominio"` → `CODCATEGORIA` correcto = `300`
  - `app_type == "amerika"` → `CODCATEGORIA` correcto = `400`
- **Lógica de corrección**:
  - Comparar `codcategoria` original con `app_type` detectado
  - Si hay discrepancia:
    - Calcular `corrected_codcategoria` según `app_type` detectado
    - **Actualizar `CODCATEGORIA` en Supabase** al valor correcto
    - Registrar en `AI_CLASSIFICATION_DATA`:
      - `original_codcategoria`: Categoría original (para auditoría)
      - `corrected_codcategoria`: Categoría corregida
      - `category_corrected: true`
    - Registrar en logs la corrección
  - Si no hay discrepancia:
    - `category_corrected: false`
    - `corrected_codcategoria: null`
    - `original_codcategoria: codcategoria`
- **Ejemplo**: Usuario selecciona categoría 300 (dominio) pero menciona "Amerika" en descripción:
  - IA detecta: `app_type = "amerika"`
  - Sistema corrige: `CODCATEGORIA = 400` en Supabase
  - Se ejecuta acción en Amerika
  - Categoría queda corregida en la solicitud
- **Nota**: Esta corrección se realiza automáticamente después de la clasificación (Paso 7.1.5) y antes de ejecutar acciones

### 9. Validación de Requisitos de Respuesta de IA (CRÍTICO - PRIMER PASO ANTES DE EJECUTAR)
- **OBJETIVO**: Validar que la respuesta de la IA contenga todos los datos requeridos y correctos antes de ejecutar acciones.
- **JUSTIFICACIÓN**: Esta validación es CRÍTICA y debe ejecutarse como PRIMER PASO después de la clasificación para garantizar que el agente funcione correctamente.
- **Referencia**: Ver FASE 3.8 (Validación de Requisitos de Respuesta de IA Antes de Ejecutar Acciones) para detalles completos.
- Llamar a `AIProcessor.validate_classification_for_execution()`:
  - Valida `app_type` coincide con el esperado
  - Valida `detected_actions` no está vacío y contiene solo acciones válidas
  - Valida `ususolicita` está presente y es válido
  - Para Amerika: Mapea `change_password` → `generate_password` (CRÍTICO)
  - Para Dominio: Valida y extrae `user_name` con formato correcto
- **Si validación falla**:
  - NO ejecutar acciones
  - Actualizar solicitud con mensaje de error claro
  - Establecer `CODESTADO = 3` (SOLUCIONADO) con mensaje de error
  - Registrar errores en logs
  - Terminar procesamiento (no continuar)
- **Si validación pasa**:
  - Guardar `execution_params` validados para uso en ejecución de acciones
  - Continuar con procesamiento normal

### 10. Extracción de Parámetros (Ya Validados)
- Los parámetros ya fueron validados y extraídos en el Paso 9
- `execution_params` contiene:
  - Para Amerika: `{"mapped_actions": [...], "user_id": "..."}`
  - Para Dominio: `{"mapped_actions": [...], "user_id": "...", "user_name": "..."}`
- Usar `execution_params` directamente en ejecución de acciones (NO reconstruir)

### 11. Ejecución de Acciones
- **Determinar aplicaciones a procesar**:
  - Si `execution_params.requires_secondary_app == True`: Procesar ambas aplicaciones secuencialmente
  - Si `execution_params.requires_secondary_app == False`: Procesar solo aplicación principal
- **Orden de ejecución**: Secuencial (una acción después de otra, no en paralelo)
- **Estrategia de continuación**: Si una acción falla, continuar con las siguientes acciones (no detener el procesamiento)
- **PASO 1: Procesar aplicación principal**:
  - **Para Dominio (`app_type == "dominio"`)**: 
    - SIEMPRE ejecutar `find_user` PRIMERO (ver FASE 5.3, Paso 7.3 para detalles)
    - Si `find_user` retorna `found: false`, NO continuar con acciones siguientes de dominio
    - Si `find_user` retorna `found: true`, continuar con acciones siguientes
  - **IMPORTANTE**: Usar `execution_params.primary_actions` o `execution_params.mapped_actions` (ya mapeadas y validadas en Paso 9)
  - **Para cada acción en acciones principales** (después de `find_user` si aplica):
  - Ejecutar acciones en orden: `change_password`/`generate_password` primero, luego `unlock_account`
  - Si `app_type == "amerika"`:
    - Llamar a `ActionExecutor.execute_amerika_action()` con:
      - `user_id`: `execution_params.user_id` (validado)
      - `action_type`: Acción de `execution_params.mapped_actions` (ya mapeada: `generate_password` o `unlock_account`)
  - Si `app_type == "dominio"`:
    - Llamar a `ActionExecutor.execute_dominio_action()` con:
      - `user_id`: `execution_params.user_id` (validado)
      - `action_type`: Acción de `execution_params.mapped_actions` (`change_password` o `unlock_account`)
      - `user_name`: `execution_params.user_name` (validado y con formato correcto)
    - Si una acción falla:
      - Registrar error en `actions_executed` con `success: false` y `app_type: "principal"`
      - Continuar con siguiente acción (no detener)
- **PASO 2: Procesar aplicación secundaria (si aplica)**:
  - Solo si `execution_params.requires_secondary_app == True`
  - **IMPORTANTE**: Usar `execution_params.secondary_app_actions` (ya mapeadas si es Amerika)
  - **Para Dominio (secundario)**: Ejecutar `find_user` PRIMERO (reutilizar `user_name` de aplicación principal)
  - **Para Amerika (secundario)**: No requiere `find_user`, ejecutar directamente
  - **Para cada acción en `execution_params.secondary_app_actions`**:
    - Ejecutar acción con `ActionExecutor` según `execution_params.secondary_app`
    - Si una acción falla:
      - Registrar error en `actions_executed` con `success: false` y `app_type: "secundaria"`
      - Continuar con siguiente acción (no detener)
- **Recopilar resultados de todas las acciones**:
  - Registrar cada acción en `AI_CLASSIFICATION_DATA.actions_executed`
  - Incluir: `app_type` ("principal" o "secundaria"), `action_type`, `success`, `result`, `timestamp`
  - Si alguna acción falló, incluir detalles del error

### 12. Generación de Mensaje de Solución
- **Nota sobre Generación de Mensajes**: Los mensajes finales se generan mediante **lógica programática (plantillas predefinidas)**, no con IA adicional. La IA (Gemini 2.5 Flash) solo se utiliza para la clasificación inicial y extracción de entidades. La generación de la bitácora final (`SOLUCION`) es programática para optimizar costos y garantizar consistencia.

- **Si se procesaron múltiples aplicaciones (`requires_secondary_app == True`)**:
  - Generar mensaje combinado que cubra ambas aplicaciones
  - Estructura: "Se procesaron sus solicitudes en ambas aplicaciones:\n\n**{APP_PRINCIPAL}**: [mensajes de acciones principales]\n\n**{APP_SECUNDARIA}**: [mensajes de acciones secundarias]"
  - Incluir contraseñas generadas de ambas aplicaciones si aplica
  - Incluir resultados de desbloqueo de ambas aplicaciones si aplica
  - Si alguna acción falló en alguna aplicación, incluir mensaje de error amigable

- **Si todas las acciones fueron exitosas (una o ambas aplicaciones)**:
  - Construir mensaje formal basado en acciones ejecutadas:
    - Si acción fue `change_password`:
      - Incluir contraseña generada
      - Mensaje: "Se ha generado una nueva contraseña para su cuenta de {app_type}. Su nueva contraseña es: {password}. Por favor, guárdela en un lugar seguro y cámbiela después de iniciar sesión."
    - Si acción fue `unlock_account`:
      - Mensaje: "Su cuenta de {app_type} ha sido desbloqueada exitosamente. Ya puede iniciar sesión normalmente."
    - Si ambas acciones:
      - Combinar mensajes: "Se ha generado una nueva contraseña para su cuenta de {app_type}: {password}. Además, su cuenta ha sido desbloqueada exitosamente. Ya puede iniciar sesión con su nueva contraseña."
  
- **Si alguna acción falló (pero otras fueron exitosas)**:
  - Generar mensaje combinado con éxito + errores:
    - Primero: Detalles de acciones exitosas (contraseñas generadas, desbloqueos confirmados)
    - Segundo: Detalles de acciones fallidas con mensajes amigables del backend
    - Ejemplo:
      ```
      "Se ha generado una nueva contraseña para su cuenta de {app_type}: {password}. 
      Sin embargo, no se pudo desbloquear su cuenta debido a: {mensaje_amigable_del_backend}. 
      Por favor, contacte al soporte si necesita asistencia adicional."
      ```
    - Incluir `action_suggestion` del backend si está disponible
  
- **Si todas las acciones fallaron**:
  - Usar mensaje amigable del backend (ver FASE 2.5)
  - Incluir información sobre reintentos automáticos si aplica
  - Mensaje: "No se pudieron completar las acciones solicitadas. {mensaje_amigable_del_backend}. {action_suggestion}"
  
- **Formato**: Profesional y claro para el usuario final

### 13. Actualización de Solicitud
- Actualizar solicitud en Supabase:
  - `CODESTADO = 3` (SOLUCIONADO)
  - `SOLUCION = mensaje_formal`
  - `FESOLUCION = ahora`
  - `CODUSOLUCION = "AGENTE-MS"`
  - `FECCIERRE = ahora`
  - `CODMOTCIERRE = 5` (Respuesta Final)
  - `AI_CLASSIFICATION_DATA = datos_completos`

### 14. Manejo de Errores
- Si cualquier paso falla:
  - **Extraer mensaje amigable del backend** (si el error proviene del backend):
    - Usar `extract_backend_error_message()` para obtener mensaje amigable y acción sugerida
    - NO exponer detalles técnicos al usuario
  - **Actualizar solicitud con mensaje amigable**:
    - `SOLUCION`: Mensaje amigable en español (del backend si está disponible)
    - Incluir `action_suggestion` si está disponible
    - `CODESTADO = 3` (SOLUCIONADO) con mensaje de error amigable
    - Agregar información técnica en `AI_CLASSIFICATION_DATA` (solo para auditoría)
  - **Registrar error en logs**:
    - Incluir detalles técnicos en logs estructurados (NO en mensaje al usuario)
    - Registrar contexto completo (user_id, action_type, endpoint, status_code)
  - **Continuar procesamiento de otras solicitudes**:
    - Un error en una solicitud no debe detener el procesamiento de otras

---

## Ejemplos de Clasificación

### Ejemplo 1: Cambio de Contraseña de Amerika
**Input**:
- `description`: "Necesito cambiar mi contraseña de Amerika porque la olvidé"
- `codcategoria`: 400
- `ususolicita`: "mzuloaga"

**Clasificación Esperada**:
```json
{
  "app_type": "amerika",
  "confidence": 0.95,
  "detected_actions": ["change_password"],
  "reasoning": "El usuario menciona explícitamente 'Amerika' y 'cambiar contraseña'",
  "extracted_params": {
    "user_id": "mzuloaga"
  }
}
```

**Acciones Ejecutadas**:
1. `ActionExecutor.execute_amerika_action(user_id="mzuloaga", action_type="generate_password")`

**Resultado**:
- Contraseña generada: `"Abc123Xyz789"`
- Mensaje: "Se ha generado una nueva contraseña para su cuenta de Amerika: Abc123Xyz789"

### Ejemplo 2: Desbloqueo de Cuenta de Dominio
**Input**:
- `description`: "Mi cuenta de dominio está bloqueada, necesito que la desbloqueen"
- `codcategoria`: 300
- `ususolicita`: "jperez"

**Clasificación Esperada**:
```json
{
  "app_type": "dominio",
  "confidence": 0.90,
  "detected_actions": ["unlock_account"],
  "reasoning": "El usuario menciona 'cuenta de dominio' y 'bloqueada'",
  "extracted_params": {
    "user_id": "jperez",
    "user_name": "jperez"
  }
}
```

**Acciones Ejecutadas**:
1. `ActionExecutor.execute_dominio_action(user_id="jperez", action_type="unlock_account", user_name="jperez")`

**Resultado**:
- Mensaje: "Su cuenta de dominio ha sido desbloqueada exitosamente. Ya puede iniciar sesión normalmente."

### Ejemplo 3: Cambio de Contraseña y Desbloqueo de Dominio
**Input**:
- `description`: "Olvidé mi contraseña de dominio y además mi cuenta está bloqueada, necesito ayuda"
- `codcategoria`: 300
- `ususolicita`: "arodriguez"

**Clasificación Esperada**:
```json
{
  "app_type": "dominio",
  "confidence": 0.92,
  "detected_actions": ["change_password", "unlock_account"],
  "reasoning": "El usuario menciona 'dominio', 'olvidé contraseña' y 'cuenta bloqueada'",
  "extracted_params": {
    "user_id": "arodriguez",
    "user_name": "arodriguez"
  }
}
```

**Acciones Ejecutadas**:
1. `ActionExecutor.execute_dominio_action(user_id="arodriguez", action_type="change_password", user_name="arodriguez")`
2. `ActionExecutor.execute_dominio_action(user_id="arodriguez", action_type="unlock_account", user_name="arodriguez")`

**Resultado**:
- Contraseña generada: `"XyZ123!@#Abc"`
- Mensaje: "Se ha generado una nueva contraseña para su cuenta de dominio: XyZ123!@#Abc. Además, su cuenta ha sido desbloqueada exitosamente."

---

## Testing y Validación

### Testing Manual

1. **Probar Clasificación de IA**:
   - Crear solicitud desde frontend
   - Verificar que el agente detecte la nueva solicitud
   - Verificar logs de clasificación
   - Verificar que `AI_CLASSIFICATION_DATA` se actualice correctamente

2. **Probar Ejecución de Acciones**:
   - Crear solicitud que requiera cambio de contraseña
   - Verificar que se ejecute la acción en el backend
   - Verificar que la contraseña se genere correctamente
   - Verificar que se actualice en la solicitud

3. **Probar Actualización de Estado**:
   - Verificar que `CODESTADO` cambie de 1 (PENDIENTE) a 2 (TRAMITE) durante procesamiento
   - Verificar que `CODESTADO` cambie a 3 (SOLUCIONADO) al finalizar
   - Verificar que `SOLUCION` contenga mensaje formal
   - Verificar que `CODUSOLUCION = "AGENTE-MS"`

### Testing Automatizado (Futuro)

1. **Tests Unitarios**:
   - Test de `ActionExecutor` con mocks del backend
   - Test de `AIProcessor` con mocks de Gemini AI
   - Test de `RealtimeListener` con mocks de Supabase

2. **Tests de Integración**:
   - Test de flujo completo con backend real
   - Test de clasificación con Gemini AI real
   - Test de actualización en Supabase real

3. **Tests E2E**:
   - Crear solicitud desde frontend
   - Verificar que el agente la procese completamente
   - Verificar que el frontend muestre el estado actualizado

---

## Notas de Implementación

### Orden de Implementación Recomendado

**⚠️ PREREQUISITOS CRÍTICOS (Implementar ANTES del Agente AI)**:

1. **Backend - FASE 4.1.1**: Mensajes de Error Amigables (`specs/03_backend_detailed.md`)
   - **CRÍTICO**: El backend debe retornar mensajes amigables en español con `action_suggestion`
   - Sin esto, el agente no podrá comunicar errores de forma clara a los usuarios
   - Verificar que todos los endpoints retornen estructura estándar de error

2. **Frontend - FASE 5.1.1**: Mejoras en Mensajes de Error Amigables (`specs/04_frontend_detailed.md`)
   - **CRÍTICO**: El frontend debe aprovechar los mensajes amigables del backend
   - Sin esto, los usuarios no verán mensajes claros cuando haya errores
   - Verificar que el frontend extraiga y muestre `action_suggestion`

**Orden de Implementación del Agente AI**:

1. **FASE 1**: Configuración del proyecto y `config.py`
2. **FASE 2.1-2.4**: `ActionExecutor` básico (permite probar integración con backend)
3. **FASE 2.5**: Manejo de Errores HTTP del Backend con Mensajes Amigables
   - **REQUIERE**: Backend FASE 4.1.1 completada
   - **REQUIERE**: Frontend FASE 5.1.1 completada
   - Implementar extracción de mensajes amigables del backend
4. **FASE 3.1**: `System Prompts` (crear prompts reutilizables primero)
5. **FASE 3.2-3.7**: `AIProcessor` (implementar procesamiento con prompts optimizados)
6. **FASE 3.8**: **Validación de Requisitos de Respuesta de IA (CRÍTICO - PRIMER PASO)** ⚠️
   - **CRÍTICO**: Esta validación debe implementarse ANTES de la FASE 5
   - **JUSTIFICACIÓN**: Garantiza que el agente funcione correctamente validando datos antes de ejecutar acciones
   - **REQUIERE**: FASE 3.2-3.7 completada (necesita `ClassificationResult` y `AIProcessor`)
   - Implementar método `validate_classification_for_execution()` en `AIProcessor`
   - Validar mapeo de acciones para Amerika (`change_password` → `generate_password`)
   - Validar `user_name` para Dominio con formato correcto
   - **SIN ESTA VALIDACIÓN, EL AGENTE NO DEBE EJECUTAR ACCIONES**
7. **FASE 4**: `RequestValidator` (validación y rate limiting - crítico para seguridad)
8. **FASE 5**: `RealtimeListener` (integra todos los componentes, incluyendo validación)
   - **REQUIERE**: FASE 3.8 completada (validación de requisitos de respuesta de IA)
   - En Paso 7.1.6, ejecutar validación de requisitos ANTES de ejecutar acciones
9. **FASE 6**: `main.py` (punto de entrada y orquestación)

**Nota sobre Optimización**: Implementar System Prompts (FASE 3.1) antes del AIProcessor permite probar y optimizar los prompts independientemente, facilitando el ajuste de tokens y estructura de respuestas.

**Nota sobre Dependencias**: La FASE 2.5 (Manejo de Errores HTTP) **DEBE** implementarse después de que el backend y frontend tengan sus mejoras de mensajes amigables. Sin estas mejoras, el agente no podrá proporcionar una experiencia de usuario adecuada cuando ocurran errores.

**⚠️ NOTA CRÍTICA SOBRE VALIDACIÓN DE REQUISITOS (FASE 3.8)**: 
- La validación de requisitos de respuesta de IA es **CRÍTICA** y debe implementarse como **PRIMER PASO** después de la clasificación.
- **SIN ESTA VALIDACIÓN, EL AGENTE NO DEBE EJECUTAR ACCIONES** en el backend.
- Esta validación garantiza que:
  - Los datos de la IA están completos y correctos
  - Las acciones están mapeadas correctamente (Amerika: `change_password` → `generate_password`)
  - Los parámetros requeridos están presentes y tienen formato válido
  - El agente no falla en el backend por datos inválidos
- **Implementar FASE 3.8 ANTES de FASE 5** para garantizar que el agente funcione correctamente desde el inicio.

### Consideraciones Importantes

1. **Prerequisitos de Backend y Frontend (CRÍTICO)**:
   - **ANTES** de implementar el Agente AI, el backend debe tener completada la FASE 4.1.1 (Mensajes de Error Amigables)
   - **ANTES** de implementar el Agente AI, el frontend debe tener completada la FASE 5.1.1 (Mejoras en Mensajes de Error Amigables)
   - El agente depende de estos mensajes amigables para comunicar errores a los usuarios
   - Sin estas mejoras, los usuarios verán mensajes técnicos o en inglés, degradando la experiencia

2. **Manejo de Errores**: El agente debe ser resiliente. Un error en una solicitud no debe detener el procesamiento de otras.

2. **Idempotencia**: El agente debe poder procesar la misma solicitud múltiples veces sin efectos secundarios (si ya está procesada, no reprocesar).

3. **Validación y Sanitización**: 
   - Todas las entradas deben ser validadas y sanitizadas antes de procesar
   - Nunca confiar en datos del evento sin validar
   - Rechazar solicitudes que no cumplan con los requisitos mínimos

4. **Filtros de Seguridad para IA (CRÍTICO)**:
   - Ejecutar filtros de seguridad ANTES de enviar a Gemini AI
   - Detectar y bloquear intentos de prompt injection
   - Detectar y bloquear instrucciones peligrosas al asistente
   - Escanear contenido malicioso (SQL injection, XSS, command injection)
   - Si se detecta riesgo ALTO o CRÍTICO: NO enviar a IA, rechazar inmediatamente
   - Registrar todos los rechazos por seguridad para auditoría

4. **Rate Limiting**: 
   - El rate limiting es crítico para prevenir abusos
   - Los límites deben ser configurables y administrables
   - Los mensajes de rechazo deben ser claros y profesionales
   - Registrar todos los rechazos por rate limiting para auditoría

5. **Logging**: Logging exhaustivo es crítico para debugging y monitoreo. Registrar todos los pasos importantes, especialmente validaciones y rechazos.

6. **Seguridad**: 
   - Nunca loggear contraseñas generadas
   - Usar `SUPABASE_SERVICE_ROLE_KEY` solo para operaciones del sistema
   - Validar y sanitizar todas las entradas antes de procesar
   - Implementar rate limiting para prevenir abusos
   - Registrar intentos de abuso o solicitudes rechazadas

7. **Performance**:
   - Procesar solicitudes de forma asíncrona
   - No bloquear el listener mientras se procesa una solicitud
   - Considerar procesamiento en paralelo si hay múltiples solicitudes

8. **Monitoreo**:
   - Registrar métricas: número de solicitudes procesadas, tiempo de procesamiento, tasa de éxito/error
   - Alertar si el agente deja de funcionar

---

## Referencias y Documentación

- [SDK de Supabase para Python](https://github.com/supabase/supabase-py)
- [SDK de Gemini AI](https://github.com/google/generative-ai-python)
- [httpx Documentation](https://www.python-httpx.org/)
- [structlog Documentation](https://www.structlog.org/)
- [Especificación del Backend](./03_backend_detailed.md)
- [Plan de Desarrollo Principal](./02_dev_plan.md)

---

## Funcionalidades Deseables (Fuera del Alcance Actual)

**Nota Importante**: Las siguientes funcionalidades son deseables para futuras implementaciones pero **NO están incluidas en el alcance de la Fase 1**. Se documentan aquí para referencia futura y planificación de fases posteriores.

### Sistema de Auditoría y Seguridad Avanzado

#### Objetivo General

Implementar un sistema completo de auditoría que permita rastrear, analizar y alertar sobre comportamientos anómalos, violaciones de seguridad y patrones de uso problemáticos de los usuarios.

#### Funcionalidades Deseables

##### 1. Auditoría de Comportamientos de Usuarios

**Descripción**: Sistema para registrar y analizar el comportamiento de los usuarios en el sistema.

**Componentes**:
- **Registro de Eventos de Auditoría**:
  - Crear tabla `HLP_AUDITORIA` o similar para almacenar eventos de auditoría
  - Campos sugeridos:
    - `CODAUDITORIA` (PK, autoincremental)
    - `USUARIO` (VARCHAR) - Usuario que generó el evento
    - `TIPO_EVENTO` (VARCHAR) - Tipo de evento (ej: "RATE_LIMIT_EXCEEDED", "INVALID_DESCRIPTION", "SUSPICIOUS_PATTERN")
    - `DESCRIPCION` (TEXT) - Descripción detallada del evento
    - `METADATA` (JSONB) - Datos adicionales del evento
    - `FECHA_EVENTO` (TIMESTAMPTZ) - Fecha y hora del evento
    - `SEVERIDAD` (SMALLINT) - Nivel de severidad (1-Bajo, 2-Medio, 3-Alto, 4-Crítico)
    - `RESUELTO` (BOOLEAN) - Si el evento fue revisado/resuelto
    - `RESUELTO_POR` (VARCHAR) - Usuario administrador que resolvió
    - `FECHA_RESOLUCION` (TIMESTAMPTZ) - Fecha de resolución

- **Eventos a Auditar**:
  - Intentos de exceder rate limiting
  - Solicitudes con descripciones inválidas o sospechosas
  - Patrones de solicitudes anómalos (muchas solicitudes en corto tiempo)
  - Cambios de estado inusuales
  - Errores repetidos del mismo usuario

##### 2. Histórico de Solicitudes y Análisis de Patrones

**Descripción**: Sistema para mantener y analizar el historial completo de solicitudes de cada usuario.

**Componentes**:
- **Vista de Histórico de Usuario**:
  - Consulta de todas las solicitudes de un usuario (histórico completo)
  - Estadísticas por usuario:
    - Número total de solicitudes
    - Frecuencia de solicitudes
    - Tipos de solicitudes más comunes
    - Tasa de éxito/resolución
    - Tiempo promedio entre solicitudes

- **Detección de Patrones Anómalos**:
  - Usuarios que generan muchas solicitudes de desbloqueo (posible problema de seguridad)
  - Usuarios que olvidan contraseñas frecuentemente (posible problema de memoria o gestión)
  - Solicitudes con patrones temporales sospechosos (ej: todas a la misma hora)
  - Comparación con promedios del sistema

##### 3. Registro de Prompts Indebidos y Violaciones de Seguridad

**Descripción**: Sistema para detectar y registrar intentos de uso indebido del sistema.

**Componentes**:
- **Detección de Prompts Indebidos**:
  - Análisis de descripciones que intentan:
    - Manipular la clasificación de la IA
    - Obtener información sensible
    - Ejecutar acciones no autorizadas
    - Bypass de validaciones
  - Uso de palabras clave sospechosas o patrones de texto maliciosos
  - Intentos de inyección de código o comandos

- **Clasificación de Violaciones**:
  - **Nivel 1 - Bajo**: Descripción con formato inusual pero no maliciosa
  - **Nivel 2 - Medio**: Intento de manipulación o bypass de validaciones
  - **Nivel 3 - Alto**: Patrón sospechoso o múltiples intentos de violación
  - **Nivel 4 - Crítico**: Evidencia clara de intento de abuso o ataque

- **Registro de Violaciones**:
  - Almacenar en tabla de auditoría con severidad correspondiente
  - Incluir descripción original, clasificación de la IA, y resultado del procesamiento
  - Vincular con el usuario que generó la solicitud

##### 4. Identificación de Usuarios con Problemas Comunes

**Descripción**: Sistema para identificar usuarios que generan bloqueos frecuentes o tienen problemas recurrentes.

**Componentes**:
- **Métricas de Usuario Problemático**:
  - Número de solicitudes de desbloqueo en un período
  - Frecuencia de bloqueos (solicitudes de desbloqueo / tiempo)
  - Patrón de bloqueos (mismo tipo de cuenta, misma hora, etc.)
  - Comparación con promedio del sistema

- **Criterios de Identificación**:
  - Usuario con más de X bloqueos en Y días (configurable)
  - Usuario que genera bloqueos con frecuencia mayor al promedio + desviación estándar
  - Usuario con múltiples solicitudes de desbloqueo del mismo tipo de cuenta
  - Usuario con historial de violaciones de seguridad

- **Perfil de Usuario Problemático**:
  - Crear tabla `HLP_USUARIOS_PROBLEMATICOS` o similar:
    - `CODUSUARIO` (VARCHAR, PK)
    - `USUARIO` (VARCHAR) - Nombre de usuario
    - `FECHA_IDENTIFICACION` (TIMESTAMPTZ) - Primera vez que se identificó
    - `ULTIMA_ACTUALIZACION` (TIMESTAMPTZ) - Última vez que se actualizó
    - `NIVEL_RIESGO` (SMALLINT) - 1-Bajo, 2-Medio, 3-Alto
    - `RAZON` (TEXT) - Razón de la identificación
    - `ESTADISTICAS` (JSONB) - Estadísticas del usuario
    - `ACCIONES_TOMADAS` (JSONB) - Historial de acciones tomadas
    - `ACTIVO` (BOOLEAN) - Si el usuario sigue siendo problemático

##### 5. Sistema de Alertas y Notificaciones

**Descripción**: Sistema para generar alertas automáticas cuando se detectan comportamientos anómalos o violaciones.

**Componentes**:
- **Tipos de Alertas**:
  - **Alerta de Rate Limit**: Cuando un usuario excede el límite de solicitudes
  - **Alerta de Patrón Sospechoso**: Cuando se detecta un patrón anómalo
  - **Alerta de Violación de Seguridad**: Cuando se detecta un intento de abuso
  - **Alerta de Usuario Problemático**: Cuando un usuario es identificado como problemático
  - **Alerta de Múltiples Fallos**: Cuando un usuario tiene múltiples solicitudes fallidas

- **Canales de Notificación**:
  - Email a administradores
  - Dashboard de alertas en tiempo real
  - Webhook para integración con sistemas externos (Slack, Teams, etc.)
  - Logs estructurados para sistemas de monitoreo (Prometheus, Grafana, etc.)

- **Configuración de Alertas**:
  - Umbrales configurables para cada tipo de alerta
  - Frecuencia de notificaciones (evitar spam)
  - Agrupación de alertas similares
  - Escalamiento de alertas (si no se resuelven)

##### 6. Dashboard de Monitoreo y Seguimiento

**Descripción**: Interfaz para visualizar y gestionar usuarios problemáticos y eventos de auditoría.

**Componentes**:
- **Vista de Usuarios Problemáticos**:
  - Lista de usuarios identificados como problemáticos
  - Filtros por nivel de riesgo, fecha, tipo de problema
  - Detalles de cada usuario (estadísticas, historial, acciones tomadas)
  - Acciones disponibles (marcar como resuelto, aumentar límites, bloquear temporalmente)

- **Vista de Eventos de Auditoría**:
  - Lista de eventos de auditoría con filtros
  - Búsqueda por usuario, tipo de evento, severidad, fecha
  - Detalles de cada evento
  - Marcado de eventos como resuelto

- **Gráficos y Estadísticas**:
  - Gráfico de eventos de auditoría por tipo y severidad
  - Gráfico de usuarios problemáticos por nivel de riesgo
  - Tendencias temporales (eventos por día/semana/mes)
  - Comparación con promedios del sistema

##### 7. Acciones Correctivas Automáticas

**Descripción**: Sistema para aplicar acciones automáticas basadas en el comportamiento del usuario.

**Componentes**:
- **Acciones Disponibles**:
  - **Aumentar Rate Limit**: Para usuarios confiables con necesidades legítimas
  - **Reducir Rate Limit**: Para usuarios con comportamiento sospechoso
  - **Bloqueo Temporal**: Bloquear temporalmente la creación de solicitudes
  - **Revisión Manual Requerida**: Marcar solicitudes para revisión manual antes de procesar
  - **Notificación al Usuario**: Enviar mensaje educativo al usuario sobre su comportamiento

- **Reglas Automáticas**:
  - Si usuario excede rate limit X veces en Y días → Reducir rate limit
  - Si usuario tiene N violaciones de seguridad → Bloqueo temporal
  - Si usuario es identificado como problemático → Revisión manual requerida
  - Si usuario mejora su comportamiento → Restaurar límites normales

#### Consideraciones de Implementación Futura

1. **Base de Datos**:
   - Crear tablas adicionales para auditoría y usuarios problemáticos
   - Índices para consultas eficientes
   - Políticas RLS para proteger datos sensibles

2. **Rendimiento**:
   - Considerar procesamiento asíncrono de análisis
   - Cache de estadísticas para evitar consultas costosas
   - Agregación de datos para análisis históricos

3. **Privacidad**:
   - Cumplir con regulaciones de protección de datos
   - Anonimización de datos para análisis agregados
   - Permisos y acceso controlado a datos de auditoría

4. **Integración**:
   - API para consultar datos de auditoría
   - Exportación de reportes
   - Integración con sistemas de SIEM (Security Information and Event Management)

#### Notas de Diseño

- Este sistema debe ser **no intrusivo** durante la Fase 1
- Las funcionalidades de auditoría pueden implementarse de forma incremental
- Priorizar funcionalidades que no afecten el rendimiento del procesamiento principal
- Considerar implementar primero el registro básico de eventos antes de análisis complejos

---

### Sistema de Recuperación y Reprocesamiento de Solicitudes con Estrategias de Fallback

#### Objetivo General

Implementar un sistema robusto de recuperación y reprocesamiento que permita al agente consultar y validar nuevamente las solicitudes que no pudieron ser procesadas por cualquier motivo (fallos de API, errores temporales, desconexiones, etc.), garantizando que ninguna solicitud válida quede sin procesar y manteniendo una experiencia fluida para el usuario incluso cuando ocurren fallos en servicios externos.

**Mejores Prácticas de Diseño**:
- **Estrategia de Fallback**: Si una API falla, mostrar un mensaje útil y mantener la experiencia fluida
- **Resiliencia**: El sistema debe recuperarse automáticamente de fallos temporales
- **Transparencia**: Los usuarios deben ser informados del estado de sus solicitudes de forma clara
- **Idempotencia**: El reprocesamiento debe ser seguro y no generar efectos secundarios

#### Funcionalidades Deseables

##### 1. Consulta Periódica de Solicitudes Pendientes o Fallidas

**Descripción**: Sistema para que el agente consulte periódicamente las solicitudes que quedaron en estados intermedios o fallaron durante el procesamiento.

**Componentes**:
- **Consulta de Solicitudes Pendientes**:
  - Consultar solicitudes con `CODESTADO = 1` (PENDIENTE) que tengan más de X minutos de antigüedad
  - Consultar solicitudes con `CODESTADO = 2` (TRAMITE) que estén en trámite por más de Y minutos (posible fallo durante procesamiento)
  - Consultar solicitudes con `CODESTADO = 3` (SOLUCIONADO) pero con `AI_CLASSIFICATION_DATA` que indique error o fallo

- **Criterios de Selección para Reprocesamiento**:
  - Solicitudes PENDIENTES con más de `RECOVERY_CHECK_INTERVAL_MINUTES` minutos sin procesar
  - Solicitudes en TRAMITE con más de `STUCK_PROCESSING_TIMEOUT_MINUTES` minutos (posible fallo durante procesamiento)
  - Solicitudes con `AI_CLASSIFICATION_DATA.error = true` o `AI_CLASSIFICATION_DATA.retry_eligible = true`
  - Solicitudes con `AI_CLASSIFICATION_DATA.last_attempt` más antiguo que `RETRY_DELAY_MINUTES`

- **Frecuencia de Consulta**:
  - Ejecutar consulta cada `RECOVERY_CHECK_INTERVAL_MINUTES` minutos (configurable, default: 15 minutos)
  - Consulta asíncrona que no bloquee el procesamiento de nuevas solicitudes
  - Priorizar solicitudes más antiguas primero

**Archivos Sugeridos**:
- `agent/services/recovery_service.py` (nuevo)
- Agregar campos a `AI_CLASSIFICATION_DATA`:
  ```json
  {
    "error": false,
    "retry_eligible": true,
    "last_attempt": "2024-01-15T10:30:00Z",
    "attempt_count": 0,
    "error_details": null,
    "recovery_metadata": {
      "failed_at": null,
      "failure_reason": null,
      "failed_service": null  // "gemini", "backend", "supabase"
    }
  }
  ```

##### 2. Validación Inteligente para Reprocesamiento

**Descripción**: Sistema para validar si una solicitud debe ser reprocesada o si ya fue procesada correctamente.

**Componentes**:
- **Validación de Estado Actual**:
  - Verificar que la solicitud aún esté en estado válido para reprocesamiento
  - Verificar que no haya sido procesada por otro agente o manualmente
  - Verificar que no haya excedido el número máximo de reintentos (`MAX_RECOVERY_ATTEMPTS`)

- **Detección de Procesamiento Duplicado**:
  - Verificar timestamp de última actualización
  - Verificar si `CODUSOLUCION` ya está establecido (indica procesamiento completo)
  - Verificar si `SOLUCION` contiene mensaje válido (indica resolución exitosa)
  - Usar locks distribuidos o campos de estado para evitar procesamiento concurrente

- **Criterios de Elegibilidad**:
  - Solicitud debe estar en estado PENDIENTE o TRAMITE
  - No debe haber excedido `MAX_RECOVERY_ATTEMPTS` (default: 3)
  - No debe haber sido procesada exitosamente previamente
  - Debe cumplir con todas las validaciones iniciales (rate limit, edad, etc.)

**Lógica de Validación**:
```python
def should_reprocess_request(request_data: dict) -> tuple[bool, str]:
    """
    Valida si una solicitud debe ser reprocesada.
    Retorna (should_reprocess: bool, reason: str)
    """
    # Verificar estado
    if request_data["CODESTADO"] not in [1, 2]:
        return False, "Solicitud ya procesada o en estado inválido"
    
    # Verificar intentos
    classification_data = request_data.get("AI_CLASSIFICATION_DATA", {})
    attempt_count = classification_data.get("attempt_count", 0)
    if attempt_count >= MAX_RECOVERY_ATTEMPTS:
        return False, f"Excedido número máximo de reintentos ({MAX_RECOVERY_ATTEMPTS})"
    
    # Verificar si ya fue resuelta
    if request_data.get("CODUSOLUCION"):
        return False, "Solicitud ya resuelta por otro proceso"
    
    # Verificar edad (si aplica)
    if not validate_request_age(request_data["FESOLICITA"]):
        return False, "Solicitud demasiado antigua para reprocesamiento"
    
    return True, "Elegible para reprocesamiento"
```

##### 3. Estrategias de Fallback para Fallos de API

**Descripción**: Implementar estrategias robustas de fallback cuando las APIs externas (Gemini, Backend, Supabase) fallan, garantizando mensajes útiles y experiencia fluida.

**Componentes**:

###### 3.1. Fallback para Fallos de Gemini AI

**Estrategias**:
- **Fallback 1 - Clasificación Basada en Categoría**:
  - Si Gemini falla, usar clasificación basada en `codcategoria`:
    - `300` → `app_type: "dominio"`
    - `400` → `app_type: "amerika"`
  - `confidence: 0.5` (indica clasificación automática)
  - `detected_actions: ["change_password"]` (acción más común y segura)
  - Mensaje al usuario: "Su solicitud está siendo procesada. Debido a una limitación temporal del sistema, se aplicó una clasificación automática."

- **Fallback 2 - Reintento con Backoff Exponencial**:
  - Reintentar hasta `MAX_RETRIES` veces con backoff exponencial
  - Si todos los reintentos fallan, aplicar Fallback 1
  - Registrar en logs cada intento fallido

- **Fallback 3 - Modo Degradado**:
  - Si Gemini está completamente no disponible, activar "modo degradado"
  - Procesar solo solicitudes con categorías claras (300 o 400)
  - Aplicar acciones predefinidas según categoría
  - Notificar a administradores sobre modo degradado

**Mensajes de Error para Usuario**:
```python
GEMINI_FALLBACK_MESSAGES = {
    "temporary_failure": "Su solicitud está siendo procesada. Estamos experimentando una demora temporal en el sistema de clasificación inteligente, pero su solicitud será atendida.",
    "degraded_mode": "Su solicitud está siendo procesada en modo simplificado. Esto puede tomar un poco más de tiempo, pero será resuelta correctamente.",
    "classification_fallback": "Su solicitud está siendo procesada con clasificación automática. Si necesita asistencia adicional, por favor contacte al equipo de soporte."
}
```

###### 3.2. Fallback para Fallos del Backend FastAPI

**Estrategias**:
- **Fallback 1 - Cola de Reintentos**:
  - Si el backend falla, agregar la solicitud a una cola de reintentos
  - Reintentar cada `RETRY_DELAY_MINUTES` minutos
  - Máximo `MAX_BACKEND_RETRIES` intentos
  - Mensaje al usuario: "Su solicitud está siendo procesada. Estamos experimentando una demora temporal en la ejecución de acciones, pero su solicitud será completada automáticamente."

- **Fallback 2 - Notificación de Demora**:
  - Actualizar solicitud con mensaje informativo:
    - `CODESTADO = 2` (TRAMITE)
    - `SOLUCION = "Su solicitud está en proceso. Debido a una demora temporal en el sistema, el procesamiento tomará más tiempo del habitual. Le notificaremos cuando esté completa."`
  - Registrar en `AI_CLASSIFICATION_DATA`:
    ```json
    {
      "backend_failure": true,
      "failure_timestamp": "2024-01-15T10:30:00Z",
      "retry_scheduled": true,
      "next_retry_at": "2024-01-15T10:45:00Z"
    }
    ```

- **Fallback 3 - Escalamiento Manual**:
  - Si el backend falla repetidamente (`MAX_BACKEND_RETRIES` alcanzado):
    - Marcar solicitud para revisión manual
    - Notificar a administradores
    - Mensaje al usuario: "Su solicitud requiere atención manual debido a una limitación temporal del sistema. Un administrador la revisará en breve."

**Mensajes de Error para Usuario**:
```python
BACKEND_FALLBACK_MESSAGES = {
    "temporary_failure": "Su solicitud está siendo procesada. Estamos experimentando una demora temporal en la ejecución de acciones técnicas, pero su solicitud será completada automáticamente.",
    "retry_scheduled": "Su solicitud está en cola de procesamiento. Se reintentará automáticamente en breve.",
    "manual_review": "Su solicitud requiere atención manual debido a una limitación temporal del sistema. Un administrador la revisará en breve y le notificará cuando esté resuelta."
}
```

###### 3.3. Fallback para Fallos de Supabase

**Estrategias**:
- **Fallback 1 - Reintento con Circuit Breaker**:
  - Implementar circuit breaker para Supabase
  - Si Supabase falla, pausar procesamiento temporalmente
  - Reintentar conexión cada `SUPABASE_RETRY_INTERVAL_SECONDS` segundos
  - Si se restaura conexión, reanudar procesamiento automáticamente

- **Fallback 2 - Cola Local de Actualizaciones**:
  - Si Supabase falla al actualizar, mantener actualizaciones en cola local
  - Cuando Supabase se restaura, sincronizar todas las actualizaciones pendientes
  - Priorizar actualizaciones más recientes

- **Fallback 3 - Notificación de Estado**:
  - Si no se puede actualizar Supabase, al menos registrar en logs locales
  - Notificar a administradores sobre fallo de Supabase
  - Mensaje al usuario (si es posible): "Su solicitud está siendo procesada. Hay una demora temporal en la actualización del sistema, pero el procesamiento continúa."

**Mensajes de Error para Usuario**:
```python
SUPABASE_FALLBACK_MESSAGES = {
    "connection_failure": "Su solicitud está siendo procesada. Estamos experimentando una demora temporal en la conexión con la base de datos, pero su solicitud será completada.",
    "update_failure": "Su solicitud está siendo procesada. Hay una demora temporal en la actualización del estado, pero el procesamiento continúa."
}
```

##### 4. Sistema de Cola de Reintentos con Priorización

**Descripción**: Implementar un sistema de cola para gestionar solicitudes que requieren reintento, con priorización inteligente.

**Componentes**:
- **Estructura de Cola**:
  - Cola priorizada por:
    1. Antigüedad de la solicitud (más antiguas primero)
    2. Número de intentos (menos intentos primero)
    3. Tipo de error (errores temporales antes que errores permanentes)
    4. Urgencia (solicitudes de desbloqueo antes que cambio de contraseña)

- **Gestión de Reintentos**:
  - Agregar solicitud a cola cuando falla
  - Programar próximo intento según backoff exponencial
  - Procesar cola periódicamente (cada `RETRY_QUEUE_PROCESS_INTERVAL_MINUTES`)
  - Remover de cola cuando se procesa exitosamente o excede `MAX_RECOVERY_ATTEMPTS`

- **Persistencia de Cola**:
  - Almacenar cola en Supabase (tabla `HLP_RETRY_QUEUE` o similar)
  - O usar almacenamiento local (Redis, SQLite) para alta disponibilidad
  - Sincronizar cola entre múltiples instancias del agente (si aplica)

**Estructura de Cola Sugerida**:
```python
class RetryQueueItem:
    codpeticiones: int
    priority: int  # Mayor = más prioritario
    next_retry_at: datetime
    attempt_count: int
    last_error: str
    error_type: str  # "gemini", "backend", "supabase", "validation"
    request_snapshot: dict  # Snapshot de la solicitud al momento del fallo
```

##### 5. Monitoreo y Alertas de Fallos

**Descripción**: Sistema para monitorear fallos y generar alertas cuando se detectan problemas recurrentes.

**Componentes**:
- **Métricas de Fallos**:
  - Tasa de fallos por servicio (Gemini, Backend, Supabase)
  - Número de solicitudes en cola de reintentos
  - Tiempo promedio de recuperación
  - Tasa de éxito después de reintento

- **Alertas Automáticas**:
  - **Alerta de Tasa de Fallo Alta**: Si tasa de fallo > `FAILURE_RATE_THRESHOLD` (default: 10%)
  - **Alerta de Cola Llena**: Si cola de reintentos > `RETRY_QUEUE_SIZE_THRESHOLD` (default: 50)
  - **Alerta de Servicio No Disponible**: Si un servicio falla por más de `SERVICE_DOWNTIME_THRESHOLD_MINUTES` (default: 30)
  - **Alerta de Modo Degradado**: Cuando se activa modo degradado

- **Dashboard de Salud del Sistema**:
  - Estado de cada servicio (Gemini, Backend, Supabase)
  - Número de solicitudes en cada estado
  - Tasa de éxito/fallo en tiempo real
  - Gráficos de tendencias de fallos

##### 6. Notificaciones al Usuario sobre Estado de Solicitud

**Descripción**: Sistema para mantener a los usuarios informados sobre el estado de sus solicitudes, especialmente cuando hay demoras o fallos.

**Componentes**:
- **Actualización de Estado en Tiempo Real**:
  - Actualizar `SOLUCION` con mensajes informativos durante procesamiento
  - Usar estados intermedios descriptivos:
    - "Su solicitud está siendo procesada..."
    - "Clasificando su solicitud con inteligencia artificial..."
    - "Ejecutando acciones técnicas..."
    - "Hay una demora temporal, pero su solicitud será completada..."

- **Mensajes Contextuales**:
  - Mensajes diferentes según el tipo de fallo
  - Mensajes que no generen ansiedad innecesaria
  - Mensajes que indiquen acción automática (no requiere intervención del usuario)

- **Notificaciones de Completado**:
  - Cuando una solicitud se completa después de un fallo inicial
  - Notificar al usuario que su solicitud fue procesada exitosamente
  - Incluir detalles de las acciones ejecutadas

**Ejemplo de Flujo de Mensajes**:
```
Estado Inicial: "Su solicitud está siendo procesada..."
Falló Gemini: "Su solicitud está siendo procesada. Estamos experimentando una demora temporal en el sistema de clasificación inteligente, pero su solicitud será atendida."
Reintentando: "Reintentando procesamiento de su solicitud..."
Completado: "Su solicitud ha sido procesada exitosamente. [Detalles de acciones]"
```

#### Consideraciones de Implementación Futura

1. **Base de Datos**:
   - Crear tabla `HLP_RETRY_QUEUE` para persistir cola de reintentos:
     - `CODRETRY` (PK, autoincremental)
     - `CODPETICIONES` (FK a HLP_PETICIONES)
     - `PRIORIDAD` (INTEGER)
     - `PROXIMO_REINTENTO` (TIMESTAMPTZ)
     - `INTENTOS` (SMALLINT)
     - `ULTIMO_ERROR` (TEXT)
     - `TIPO_ERROR` (VARCHAR)
     - `SNAPSHOT_SOLICITUD` (JSONB)
   - Índices en `PROXIMO_REINTENTO` y `PRIORIDAD` para consultas eficientes
   - Campo `AI_CLASSIFICATION_DATA.recovery_metadata` en `HLP_PETICIONES`

2. **Configuración**:
   - Agregar a `Settings`:
     - `RECOVERY_CHECK_INTERVAL_MINUTES: int = 15`
     - `STUCK_PROCESSING_TIMEOUT_MINUTES: int = 30`
     - `MAX_RECOVERY_ATTEMPTS: int = 3`
     - `RETRY_QUEUE_PROCESS_INTERVAL_MINUTES: int = 5`
     - `MAX_BACKEND_RETRIES: int = 5`
     - `SUPABASE_RETRY_INTERVAL_SECONDS: int = 30`
     - `FAILURE_RATE_THRESHOLD: float = 0.1` (10%)
     - `RETRY_QUEUE_SIZE_THRESHOLD: int = 50`
     - `SERVICE_DOWNTIME_THRESHOLD_MINUTES: int = 30`

3. **Rendimiento**:
   - Procesar cola de reintentos de forma asíncrona
   - Limitar número de reintentos concurrentes para no sobrecargar servicios
   - Implementar rate limiting en reintentos para evitar spam a servicios externos
   - Cache de estado de servicios para evitar consultas innecesarias

4. **Resiliencia**:
   - Implementar circuit breaker para cada servicio externo
   - Detectar y aislar servicios que fallan repetidamente
   - Implementar health checks periódicos para servicios externos
   - Fallback graceful cuando todos los servicios fallan

5. **Experiencia de Usuario**:
   - Mensajes claros y no técnicos
   - Indicar que el sistema está trabajando automáticamente
   - No requerir acción del usuario durante fallos temporales
   - Notificar cuando se complete después de un fallo

#### Mejores Prácticas de Diseño

1. **Principio de Fallback Gradual**:
   - Siempre tener un fallback disponible
   - Fallback debe ser funcional aunque sea limitado
   - Fallback debe mantener la experiencia del usuario

2. **Transparencia sin Ansiedad**:
   - Informar al usuario sobre demoras, pero de forma tranquilizadora
   - Indicar que el sistema está trabajando automáticamente
   - No exponer detalles técnicos innecesarios

3. **Idempotencia**:
   - Todos los reintentos deben ser idempotentes
   - Verificar estado antes de reprocesar
   - No generar efectos secundarios duplicados

4. **Observabilidad**:
   - Registrar todos los fallos y reintentos
   - Métricas claras de salud del sistema
   - Alertas proactivas antes de que el problema se agrave

5. **Recuperación Automática**:
   - El sistema debe recuperarse automáticamente cuando sea posible
   - No requerir intervención manual para fallos temporales
   - Escalar a intervención manual solo cuando sea necesario

#### Notas de Diseño

- Este sistema debe ser **complementario** al procesamiento en tiempo real
- No debe interferir con el procesamiento normal de nuevas solicitudes
- Debe ser **eficiente** y no consumir recursos excesivos
- Las estrategias de fallback deben ser **probadas regularmente** para asegurar que funcionan
- Los mensajes al usuario deben ser **revisados periódicamente** para mantener claridad y utilidad

---

### Capa de Abstracción de APIs para Migración POC → Producción

#### Objetivo General

Implementar una capa de abstracción (Service Layer/Repository Pattern) que permita cambiar fácilmente entre el entorno de POC (simulado) y producción sin modificar la lógica del agente. Esto facilita la migración cuando se supere la POC y se integren las APIs reales de Amerika y Dominio.

**Justificación**: Actualmente, el `ActionExecutor` realiza llamadas HTTP directas al backend simulado. Cuando se migre a producción, las APIs de Amerika y Dominio pueden tener:
- URLs diferentes (microservicios separados)
- Métodos de autenticación diferentes (OAuth, Bearer tokens, etc.)
- Estructuras de respuesta ligeramente diferentes
- Endpoints diferentes

Sin una capa de abstracción, estos cambios requerirían modificar el código del agente en múltiples lugares, aumentando el riesgo de errores y dificultando el mantenimiento.

#### Funcionalidades Deseables

##### 1. Interfaces Base para APIs (Protocols/ABCs)

**Descripción**: Definir interfaces que establezcan el contrato para las APIs de Amerika y Dominio, independientemente de la implementación.

**Componentes**:
- **Interfaz `AmerikaAPIInterface`**:
  - Método `execute_action(user_id: str, action_type: Literal[...]) -> Dict[str, Any]`
  - Define estructura de respuesta esperada
  - Documenta tipos de acción soportados

- **Interfaz `DominioAPIInterface`**:
  - Método `execute_action(user_id: str, action_type: Literal[...], user_name: Optional[str]) -> Dict[str, Any]`
  - Define estructura de respuesta esperada
  - Documenta tipos de acción soportados

- **Ubicación**: `agent/services/api_interfaces.py`

**Ventajas**:
- Contrato claro entre el agente y las APIs
- Facilita testing con mocks
- Permite múltiples implementaciones sin cambiar código del agente

##### 2. Implementaciones por Entorno

**Descripción**: Crear implementaciones específicas de las interfaces para cada entorno (POC y producción).

**Componentes**:
- **Implementación POC**:
  - `POCAmerikaAPI`: Implementa `AmerikaAPIInterface` usando backend FastAPI simulado
  - `POCDominioAPI`: Implementa `DominioAPIInterface` usando backend FastAPI simulado
  - Usa `httpx.AsyncClient` para llamadas HTTP
  - Autenticación con `X-API-Key` header

- **Implementación Producción**:
  - `ProdAmerikaAPI`: Implementa `AmerikaAPIInterface` usando APIs reales de Amerika
  - `ProdDominioAPI`: Implementa `DominioAPIInterface` usando APIs reales de Dominio
  - Puede usar diferentes métodos de autenticación (OAuth, Bearer tokens, etc.)
  - Puede llamar a diferentes URLs (microservicios separados)

- **Ubicación**: `agent/services/api_implementations/`
  - `poc_amerika_api.py`
  - `poc_dominio_api.py`
  - `prod_amerika_api.py` (stub para implementación futura)
  - `prod_dominio_api.py` (stub para implementación futura)

**Ventajas**:
- Separación clara entre entornos
- Fácil agregar nuevos entornos (staging, dev, etc.)
- Implementación de producción no afecta código de POC

##### 3. Factory Pattern para Selección de Implementación

**Descripción**: Crear factory que instancie la implementación correcta según el entorno configurado.

**Componentes**:
- **Función `create_amerika_api() -> AmerikaAPIInterface`**:
  - Lee `ENVIRONMENT` de configuración
  - Retorna `POCAmerikaAPI` si `ENVIRONMENT == "poc"`
  - Retorna `ProdAmerikaAPI` si `ENVIRONMENT == "production"`
  - Lanza excepción si entorno no válido

- **Función `create_dominio_api() -> DominioAPIInterface`**:
  - Similar a `create_amerika_api()` pero para Dominio

- **Ubicación**: `agent/services/api_factory.py`

**Ventajas**:
- Cambio de entorno mediante variable de configuración
- Centraliza lógica de selección de implementación
- Fácil agregar nuevos entornos

##### 4. Configuración de Entorno y URLs

**Descripción**: Extender configuración para soportar diferentes entornos y URLs específicas por API.

**Componentes**:
- **Variables de Entorno**:
  - `ENVIRONMENT: Literal["poc", "production"] = "poc"` - Entorno actual
  - `AMERIKA_API_URL: Optional[str] = None` - URL específica para API Amerika (override de `BACKEND_URL`)
  - `DOMINIO_API_URL: Optional[str] = None` - URL específica para API Dominio (override de `BACKEND_URL`)
  - `AMERIKA_API_AUTH_TYPE: Literal["api_key", "oauth", "bearer"] = "api_key"` - Tipo de autenticación
  - `DOMINIO_API_AUTH_TYPE: Literal["api_key", "oauth", "bearer"] = "api_key"` - Tipo de autenticación
  - `AMERIKA_API_AUTH_TOKEN: Optional[str] = None` - Token de autenticación (si aplica)
  - `DOMINIO_API_AUTH_TOKEN: Optional[str] = None` - Token de autenticación (si aplica)

- **Ubicación**: `agent/core/config.py`

**Ventajas**:
- Configuración flexible por entorno
- Soporte para diferentes métodos de autenticación
- URLs específicas por API (útil cuando se migre a microservicios)

##### 5. Refactorización de ActionExecutor

**Descripción**: Modificar `ActionExecutor` para usar la capa de abstracción en lugar de llamadas HTTP directas.

**Componentes**:
- **Cambios en `ActionExecutor`**:
  - Eliminar cliente `httpx.AsyncClient` directo
  - Inicializar con instancias de `AmerikaAPIInterface` y `DominioAPIInterface` (obtenidas del factory)
  - Métodos `execute_amerika_action()` y `execute_dominio_action()` delegan a las interfaces
  - Mantener lógica de reintentos y manejo de errores envolviendo las llamadas a las APIs

- **Ubicación**: `agent/services/action_executor.py` (refactorizado)

**Ventajas**:
- Código más limpio y mantenible
- Separación de responsabilidades
- Fácil testear con mocks

##### 6. Documentación y Guía de Migración

**Descripción**: Crear documentación que explique cómo implementar las APIs de producción cuando se migre.

**Componentes**:
- **Archivo `agent/services/api_implementations/README.md`**:
  - Guía paso a paso para implementar `ProdAmerikaAPI` y `ProdDominioAPI`
  - Ejemplos de estructura de respuestas esperadas
  - Notas sobre autenticación OAuth/Bearer si aplica
  - Checklist de migración
  - Ejemplos de código

- **Stubs de Implementación**:
  - Archivos `prod_amerika_api.py` y `prod_dominio_api.py` con estructura base y TODOs
  - Facilita inicio de implementación

**Ventajas**:
- Facilita migración cuando llegue el momento
- Reduce tiempo de implementación
- Documenta decisiones de diseño

#### Estructura de Archivos Propuesta

```
agm-desk-ai/
├── agent/
│   ├── services/
│   │   ├── api_interfaces.py              # Interfaces base (nuevo)
│   │   ├── api_factory.py                 # Factory pattern (nuevo)
│   │   ├── api_implementations/           # Implementaciones por entorno (nuevo)
│   │   │   ├── __init__.py
│   │   │   ├── poc_amerika_api.py         # Implementación POC
│   │   │   ├── poc_dominio_api.py         # Implementación POC
│   │   │   ├── prod_amerika_api.py         # Stub para producción
│   │   │   ├── prod_dominio_api.py         # Stub para producción
│   │   │   └── README.md                   # Guía de migración
│   │   ├── action_executor.py             # Refactorizado para usar interfaces
│   │   └── ...
```

#### Consideraciones de Implementación Futura

1. **Compatibilidad con Backend Actual**:
   - La implementación POC debe mantener compatibilidad con el backend FastAPI simulado actual
   - No debe requerir cambios en el backend durante la Fase 1

2. **Migración Gradual**:
   - Implementar primero la capa de abstracción con implementación POC
   - Refactorizar `ActionExecutor` para usar la nueva capa
   - Cuando se migre a producción, implementar `ProdAmerikaAPI` y `ProdDominioAPI`
   - Cambiar `ENVIRONMENT=production` en configuración

3. **Testing**:
   - Crear mocks de las interfaces para testing unitario
   - Tests de integración con implementación POC
   - Tests de integración con implementación producción (cuando esté disponible)

4. **Rendimiento**:
   - La capa de abstracción no debe agregar overhead significativo
   - Mantener eficiencia de llamadas HTTP
   - Considerar connection pooling si aplica

5. **Manejo de Errores**:
   - Las interfaces deben definir excepciones estándar
   - Las implementaciones deben mapear errores específicos a excepciones estándar
   - Mantener mensajes de error amigables independientemente de la implementación

#### Beneficios Esperados

1. **Facilidad de Migración**:
   - Cambio de entorno mediante variable de configuración
   - No requiere modificar código del agente
   - Implementación de producción aislada

2. **Mantenibilidad**:
   - Separación clara de responsabilidades
   - Código más limpio y organizado
   - Fácil agregar nuevos entornos o APIs

3. **Testabilidad**:
   - Fácil mockear interfaces para tests
   - Tests independientes de implementación específica
   - Mejor cobertura de tests

4. **Extensibilidad**:
   - Fácil agregar nuevos entornos (staging, dev, etc.)
   - Fácil agregar nuevas APIs siguiendo el mismo patrón
   - Soporte para diferentes métodos de autenticación

5. **Reducción de Riesgos**:
   - Cambios en APIs de producción no afectan código del agente
   - Implementación de producción probada independientemente
   - Rollback fácil cambiando variable de entorno

#### Notas de Diseño

- Esta funcionalidad debe implementarse **después** de completar la Fase 1 del agente
- La implementación POC puede desarrollarse en paralelo con la Fase 1, pero no es crítica
- La implementación de producción debe desarrollarse cuando se tenga acceso a las APIs reales
- Mantener compatibilidad hacia atrás durante la transición
- Documentar todas las decisiones de diseño para facilitar mantenimiento futuro

---

**Fin del Documento**

