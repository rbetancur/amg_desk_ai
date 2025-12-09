# Especificación Detallada: Backend Unificado (FastAPI)

Este documento detalla la implementación del Backend Unificado usando FastAPI, expandiendo el Paso 2 del plan de desarrollo principal con especificaciones técnicas completas.

## Descripción

Desarrollar el Backend Unificado usando FastAPI. Este servicio debe validar la autenticación de Supabase y exponer los endpoints de acción que serán consumidos por el Agente AI.

**Contexto**: Este backend es un servicio monolítico modular que maneja la Mesa de Servicio (CRUD de solicitudes) y los endpoints simulados de Amerika y Dominio que serán consumidos por el Agente AI.

**Referencias**:
- [Plan de Desarrollo Principal](./02_dev_plan.md#paso-2-backend-unificado-fastapi-equipo-backend)
- [Estructura del Backend](../docs/README.md#estructura-del-backend-unificado-agm-simulated-enviromentbackend)
- [Mapeo de Nomenclatura](../docs/NAMING_MAPPING.md)

---

## FASE 1: Endpoints de Acción Simulados (Amerika y Dominio)

**Justificación**: Estos endpoints son más simples porque no requieren autenticación JWT ni acceso directo a la base de datos. Solo simulan acciones que el Agente AI ejecutará. Se implementan primero para establecer la estructura base del proyecto.

### 1.1. Configuración de Autenticación por API Key

**Objetivo**: Implementar un sistema de autenticación simple por API Key para proteger los endpoints de acción.

**Tareas**:
1. Agregar `API_SECRET_KEY` a `app/core/config.py` (Settings)
2. Agregar `CORS_ORIGINS` a `app/core/config.py` (Settings):
   - Tipo: `str` (separado por comas) o `List[str]`
   - Ejemplo: `"https://app.vercel.app,http://localhost:3000"`
   - Usar para configurar CORS en FastAPI
3. Crear dependency `get_api_key()` en `app/services/auth_service.py` que:
   - Extraiga el header `X-API-Key` o `Authorization: Bearer <key>`
   - Valide contra `settings.API_SECRET_KEY`
   - Retorne `HTTPException(401)` si es inválido
4. Configurar CORS en `app/main.py`:
   - Importar `CORSMiddleware` de `fastapi.middleware.cors`
   - Agregar middleware con:
     - `allow_origins`: Parsear `settings.CORS_ORIGINS` (split por comas si es string)
     - `allow_credentials`: `True`
     - `allow_methods`: `["GET", "POST", "PATCH", "OPTIONS"]`
     - `allow_headers`: `["Authorization", "Content-Type", "X-API-Key"]`
5. Documentar en `.env.example` las variables `API_SECRET_KEY` y `CORS_ORIGINS` (ver sección "Variables de Entorno")

**Archivos a modificar**:
- `agm-simulated-enviroment/backend/app/core/config.py`
- `agm-simulated-enviroment/backend/app/services/auth_service.py`
- `agm-simulated-enviroment/backend/app/main.py`
- `agm-simulated-enviroment/backend/.env.example` (ver sección "Variables de Entorno" para contenido completo)

### 1.2. Endpoint de Acción: Amerika

**Objetivo**: Implementar `POST /api/apps/amerika/execute-action` que simule las acciones de la aplicación Amerika.

**Acciones soportadas**:
- `generate_password`: Generar nueva contraseña alfanumérica (10-25 caracteres)
- `unlock_account`: Desbloquear cuenta de usuario
- `lock_account`: Bloquear cuenta de usuario

**Tareas**:
1. Crear esquemas Pydantic en `app/models/schemas.py`:
   - `AmerikaActionRequest`: `user_id` (str), `action_type` (Literal["generate_password", "unlock_account", "lock_account"])
   - `AmerikaActionResponse`: `success` (bool), `action_type` (str), `result` (dict), `message` (str), `generated_password` (Optional[str])
   - `AmerikaPasswordResult`: `password_length` (int), `generated_at` (str ISO8601)
   - `AmerikaAccountResult`: `account_status` (str), `action_timestamp` (str ISO8601)
2. Crear función helper `generate_password_amerika()` en `app/services/password_service.py` (nuevo archivo):
   - Usar biblioteca `secrets` de Python (criptográficamente segura)
   - Caracteres permitidos: letras minúsculas (a-z), letras mayúsculas (A-Z), números (0-9)
   - Longitud: aleatoria entre 10 y 25 caracteres (inclusive)
   - Algoritmo: `secrets.choice()` para seleccionar caracteres aleatoriamente
   - Garantizar que la contraseña contenga al menos una letra y un número
3. Implementar router en `app/routers/app_amerika.py`:
   - Endpoint `POST /api/apps/amerika/execute-action`
   - Proteger con `Depends(get_api_key)`
   - Validar `action_type` contra valores permitidos
   - Simular procesamiento (sleep 2 segundos)
   - Si `action_type == "generate_password"`:
     - Llamar a `generate_password_amerika()` para generar contraseña
     - Estructura de `result`: `{"password_length": int, "generated_at": str ISO8601}`
   - Si `action_type == "unlock_account"` o `"lock_account"`:
     - Estructura de `result`: `{"account_status": "unlocked"|"locked", "action_timestamp": str ISO8601}`
   - Retornar respuesta estructurada según formato definido (ver sección "Estructura de Respuestas")
3. Registrar router en `app/main.py` con prefix `/api/apps/amerika`

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/backend/app/routers/app_amerika.py`
- `agm-simulated-enviroment/backend/app/models/schemas.py`
- `agm-simulated-enviroment/backend/app/services/password_service.py` (nuevo)
- `agm-simulated-enviroment/backend/app/main.py`

### 1.3. Endpoint de Acción: Dominio

**Objetivo**: Implementar `POST /api/apps/dominio/execute-action` que simule las acciones del dominio corporativo.

**Acciones soportadas**:
- `find_user`: Consultar usuario por nombre de funcionario
- `change_password`: Cambiar contraseña (mínimo 10 caracteres, mayúsculas, minúsculas, números, símbolos opcionales)
- `unlock_account`: Desbloquear cuenta de usuario

**Tareas**:
1. Crear esquemas Pydantic en `app/models/schemas.py`:
   - `DominioActionRequest`: `user_id` (str), `action_type` (Literal["find_user", "change_password", "unlock_account"]), `user_name` (Optional[str] para find_user)
   - `DominioActionResponse`: `success` (bool), `action_type` (str), `result` (dict), `message` (str), `generated_password` (Optional[str])
   - `DominioFindUserResult`: `user_id` (str), `user_name` (str), `email` (str), `status` (str), `found` (bool)
   - `DominioPasswordResult`: `password_length` (int), `changed_at` (str ISO8601)
   - `DominioAccountResult`: `account_status` (str), `action_timestamp` (str ISO8601)
2. Crear función helper `generate_password_dominio()` en `app/services/password_service.py`:
   - Usar biblioteca `secrets` de Python (criptográficamente segura)
   - Caracteres permitidos: letras minúsculas (a-z), letras mayúsculas (A-Z), números (0-9), símbolos opcionales (*.?!#&$)
   - Longitud: mínimo 10 caracteres, recomendado 12-16 caracteres
   - Requisitos obligatorios: debe incluir al menos una mayúscula, una minúscula y un número
   - Símbolos: opcionales (pueden incluirse aleatoriamente con probabilidad 30%)
   - Algoritmo: generar contraseña y validar que cumple requisitos, regenerar si no cumple (máximo 10 intentos)
3. Implementar router en `app/routers/app_domain.py`:
   - Endpoint `POST /api/apps/dominio/execute-action`
   - Proteger con `Depends(get_api_key)`
   - Validar `action_type` contra valores permitidos
   - Simular procesamiento (sleep 2 segundos)
   - Si `action_type == "find_user"`:
     - Validar que `user_name` esté presente en request
     - Simular búsqueda: buscar por `user_name` (búsqueda parcial, case-insensitive)
     - Si encuentra: `result = {"user_id": "simulated_user_id", "user_name": str, "email": f"{user_name}@aguasdemanizales.com.co", "status": "active", "found": true}`
     - Si no encuentra: `result = {"user_id": None, "user_name": str, "email": None, "status": None, "found": false}`
   - Si `action_type == "change_password"`:
     - Llamar a `generate_password_dominio()` para generar contraseña
     - Estructura de `result`: `{"password_length": int, "changed_at": str ISO8601}`
   - Si `action_type == "unlock_account"`:
     - Estructura de `result`: `{"account_status": "unlocked", "action_timestamp": str ISO8601}`
   - Retornar respuesta estructurada según formato definido (ver sección "Estructura de Respuestas")
3. Registrar router en `app/main.py` con prefix `/api/apps/dominio`

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/backend/app/routers/app_domain.py`
- `agm-simulated-enviroment/backend/app/models/schemas.py`
- `agm-simulated-enviroment/backend/app/services/password_service.py` (nuevo o actualizar si ya existe)
- `agm-simulated-enviroment/backend/app/main.py`

### 1.4. Estructura de Respuestas de Endpoints de Acción

**Objetivo**: Definir estructuras exactas de respuestas de éxito y error para todos los endpoints de acción.

**Estructura de Respuesta de Éxito**:

```json
{
  "success": true,
  "action_type": "generate_password",
  "message": "Contraseña generada exitosamente",
  "result": {
    "password_length": 15,
    "generated_at": "2024-01-15T10:30:00Z"
  },
  "generated_password": "aB3xY9mK2pQ7wN" // Solo presente si action_type genera contraseña
}
```

**Estructura de Respuesta de Error**:

```json
{
  "success": false,
  "action_type": "generate_password",
  "message": "Error al generar contraseña",
  "error": "invalid_action_type",
  "detail": "El tipo de acción especificado no es válido"
}
```

**Estructuras de `result` por Acción**:

1. **Amerika - `generate_password`**:
```json
{
  "password_length": 15,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

2. **Amerika - `unlock_account` o `lock_account`**:
```json
{
  "account_status": "unlocked", // o "locked"
  "action_timestamp": "2024-01-15T10:30:00Z"
}
```

3. **Dominio - `find_user`**:
```json
{
  "user_id": "simulated_user_123",
  "user_name": "mzuloaga",
  "email": "mzuloaga@aguasdemanizales.com.co",
  "status": "active",
  "found": true
}
```
Si no se encuentra: `{"user_id": null, "user_name": "nombre_buscado", "email": null, "status": null, "found": false}`

4. **Dominio - `change_password`**:
```json
{
  "password_length": 12,
  "changed_at": "2024-01-15T10:30:00Z"
}
```

5. **Dominio - `unlock_account`**:
```json
{
  "account_status": "unlocked",
  "action_timestamp": "2024-01-15T10:30:00Z"
}
```

**Códigos HTTP**:
- `200 OK`: Acción ejecutada exitosamente
- `400 Bad Request`: Request inválido (ej: `action_type` no reconocido, `user_name` faltante para `find_user`)
- `401 Unauthorized`: API Key inválida o faltante
- `422 Unprocessable Entity`: Validación de datos fallida
- `500 Internal Server Error`: Error interno del servidor

**Implementación**:
- Crear esquemas Pydantic específicos para cada tipo de `result` (ver tareas en 1.2 y 1.3)
- Usar `datetime.utcnow().isoformat() + "Z"` para timestamps ISO8601
- Validar que `generated_password` solo esté presente cuando `action_type` genera contraseña

---

## FASE 2: Autenticación JWT de Supabase

**Justificación**: La autenticación JWT es necesaria antes de implementar el CRUD de Mesa de Servicio, ya que todos los endpoints de solicitudes requieren validar que el usuario esté autenticado.

### 2.1. Servicio de Validación JWT

**Objetivo**: Crear un servicio reutilizable para validar tokens JWT de Supabase y extraer información del usuario.

**Tareas**:
1. Agregar configuración de Supabase a `app/core/config.py`:
   - `SUPABASE_URL` (ya existe)
   - `SUPABASE_ANON_KEY` (ya existe, necesario para validar JWT de usuarios)
   - `SUPABASE_SERVICE_ROLE_KEY` (ya existe, solo para operaciones del sistema - ver sección "Estrategias de Autenticación")
2. Crear función `verify_supabase_jwt()` en `app/services/auth_service.py`:
   - Usar `python-jose` para decodificar y validar el JWT
   - **Usar `SUPABASE_ANON_KEY` para verificar la firma del token** (esta es la clave correcta para validar tokens emitidos por Supabase)
   - Extraer `sub` (user ID), `email`, y metadata del token
   - Validar expiración del token
   - Retornar objeto con información del usuario o lanzar `HTTPException(401)` si el token es inválido
3. Crear dependency `get_current_user()` en `app/services/auth_service.py`:
   - Extraer token del header `Authorization: Bearer <token>`
   - Llamar a `verify_supabase_jwt()` con `SUPABASE_ANON_KEY`
   - Validar formato de email usando biblioteca `email-validator` o regex estándar
   - Si email inválido: lanzar `HTTPException(422, "Formato de email inválido")`
   - Extraer email del token y obtener username (parte antes de `@`) usando `extract_username_from_email()`
   - Validar que username no exceda 25 caracteres (límite de `USUSOLICITA`)
   - Si excede: lanzar `HTTPException(422, "Username excede 25 caracteres")` (NO truncar para evitar colisiones)
   - Retornar objeto con información del usuario autenticado incluyendo `ususolicita` (username extraído del email)

**Archivos a modificar**:
- `agm-simulated-enviroment/backend/app/services/auth_service.py`
- `agm-simulated-enviroment/backend/app/core/config.py`

**Nota sobre USUSOLICITA**: Se extrae el username del email del usuario (parte antes de `@`). Ejemplo: `mzuloaga@aguasdemanizales.com.co` → `mzuloaga`. Para la PoC, se soportan cualquier dominio de email (incluido `gmail.com`). **IMPORTANTE**: Si el username excede 25 caracteres, se debe lanzar error de validación (`HTTPException(422)`) y NO truncar automáticamente, ya que el truncamiento puede causar colisiones de usuarios.

---

## FASE 3: Endpoints CRUD de Mesa de Servicio

**Justificación**: Estos endpoints dependen de la autenticación JWT implementada en la Fase 2. Permiten al Frontend crear y consultar solicitudes.

### 3.1. Esquemas Pydantic para Solicitudes

**Objetivo**: Expandir los esquemas existentes con validaciones y helpers para conversión de estados.

**Tareas**:
1. Verificar y completar esquemas en `app/models/schemas.py`:
   - `RequestCreate`: 
     - `codcategoria`: Validar que existe en HLP_CATEGORIAS (usar validator de Pydantic que consulta BD)
     - `description`: Validar que no esté vacío, longitud máxima 4000 caracteres (`Field(..., min_length=1, max_length=4000)`)
   - `RequestResponse`: Incluir todos los campos de `Request` entity
   - `RequestUpdate`: Permitir actualizar `codestado`, `solucion`, `fesolucion`, `codusolucion`, `feccierre`, `ai_classification_data`
   - `AIClassificationData`: Esquema Pydantic para `ai_classification_data` con estructura:
     - `app_type`: Literal["amerika", "dominio"]
     - `confidence`: float (0.0-1.0)
     - `classification_timestamp`: str (ISO8601)
     - `detected_actions`: List[str] (ej: ["generate_password", "unlock_account"])
     - `raw_classification`: Optional[str] (texto original de clasificación)
2. Crear helper functions en `app/models/schemas.py`:
   - `estado_to_text(codestado: Optional[int]) -> str`: Convierte 1→"Pendiente", 2→"En Trámite", 3→"Solucionado"
   - `text_to_estado(text: str) -> int`: Conversión inversa (opcional, para frontend)
3. Crear esquema `PaginationParams` en `app/models/schemas.py`:
   - `limit`: int (default=50, ge=1, le=100)
   - `offset`: int (default=0, ge=0)
4. Crear esquema `PaginatedResponse` genérico en `app/models/schemas.py`:
   - `items`: List[T]
   - `pagination`: `PaginationMeta` con `total`, `limit`, `offset`, `has_more`

**Archivos a modificar**:
- `agm-simulated-enviroment/backend/app/models/schemas.py`

### 3.2. Router de Mesa de Servicio

**Objetivo**: Implementar endpoints CRUD completos para gestionar solicitudes.

**Endpoints a implementar**:
- `GET /api/requests`: Listar solicitudes del usuario autenticado (con paginación opcional)
- `POST /api/requests`: Crear nueva solicitud (asignar `USUSOLICITA` desde JWT)
- `GET /api/requests/{id}`: Obtener solicitud específica (solo si pertenece al usuario)
- `PATCH /api/requests/{id}`: Actualizar solicitud (solo si pertenece al usuario, campos limitados)

**Tareas**:
1. Implementar router en `app/routers/service_desk.py`:
   - Todos los endpoints protegidos con `Depends(get_current_user)`
   - `GET /api/requests`:
     - Filtrar por `USUSOLICITA == usuario_autenticado.ususolicita` (username extraído del email)
     - **Paginación**:
       - Query params: `?limit=50&offset=0`
       - Valores por defecto: `limit=50`, `offset=0`
       - Valores máximos: `limit_max=100` (si se excede, usar 100)
       - Validar que `limit` y `offset` sean enteros no negativos
       - Crear esquema Pydantic `PaginationParams` con validaciones
     - Retornar estructura paginada:
       ```json
       {
         "items": [RequestResponse, ...],
         "pagination": {
           "total": 150,
           "limit": 50,
           "offset": 0,
           "has_more": true
         }
       }
       ```
     - Calcular `total` con `SELECT COUNT(*)` antes de aplicar limit/offset
     - `has_more = (offset + limit) < total`
   - `POST /api/requests`:
     - Validar `RequestCreate` con Pydantic
     - Obtener usuario autenticado desde `get_current_user()` (que retorna `ususolicita` extraído del email)
     - Asignar `USUSOLICITA = usuario_autenticado.ususolicita`
     - Establecer `FESOLICITA = NOW()` automáticamente
     - Establecer `CODESTADO = 1` (PENDIENTE) por defecto
     - Verificar que `codcategoria` existe en `HLP_CATEGORIAS`:
       - Query: `SELECT codcategoria FROM HLP_CATEGORIAS WHERE codcategoria = :codcategoria`
       - Usar `session.execute(select(Category).where(Category.codcategoria == codcategoria))`
       - Si no existe: lanzar `HTTPException(422, f"Categoría {codcategoria} no existe")`
       - **Optimización**: Considerar cachear categorías válidas en memoria (dict) para evitar queries repetidas
     - Insertar en BD usando SQLAlchemy
     - Retornar `RequestResponse` con el registro creado
   - `GET /api/requests/{id}`:
     - Validar que `USUSOLICITA` coincida con usuario autenticado
     - Retornar `RequestResponse` o `HTTPException(404)` si no existe o no pertenece al usuario
   - `PATCH /api/requests/{id}`:
     - Validar que `USUSOLICITA` coincida con usuario autenticado
     - Validar transición de estado si se actualiza `codestado`:
       - Llamar a `validate_state_transition(current_state, new_state)` antes de actualizar
       - Si transición no permitida: lanzar `HTTPException(422, "Transición de estado no permitida")`
     - Permitir actualizar solo campos en `RequestUpdate`
     - Retornar `RequestResponse` actualizado
2. Registrar router en `app/main.py` con prefix `/api/requests`
3. Implementar manejo de errores con códigos HTTP estándar:
   - `400 Bad Request`: Request mal formado (ej: JSON inválido, parámetros faltantes)
   - `401 Unauthorized`: Token JWT inválido, expirado o faltante
   - `403 Forbidden`: Acceso denegado (solicitud no pertenece al usuario autenticado)
   - `404 Not Found`: Recurso no encontrado (solicitud no existe o no pertenece al usuario)
   - `422 Unprocessable Entity`: Validación de datos fallida (ej: categoría no existe, transición de estado no permitida, description excede 4000 caracteres)
   - `500 Internal Server Error`: Error interno del servidor (errores de BD, excepciones no manejadas)
   
   **Estructura de respuesta de error** (usar `create_error_response()`):
   ```json
   {
     "error": "request_not_found",
     "message": "La solicitud solicitada no existe o no tienes permisos para accederla",
     "detail": "Request ID 123 not found for user mzuloaga",
     "timestamp": "2024-01-15T10:30:00Z"
   }
   ```

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/backend/app/routers/service_desk.py`
- `agm-simulated-enviroment/backend/app/main.py`

### 3.3. Integración con Base de Datos

**Objetivo**: Asegurar que los endpoints usen correctamente SQLAlchemy para acceder a Supabase.

**Tareas**:
1. Verificar que `app/db/base.py` esté configurado correctamente:
   - Engine asíncrono usando `DATABASE_URL`
   - `AsyncSessionLocal` configurado
   - `get_db()` dependency funcionando
2. En los routers, usar `Depends(get_db)` para inyectar sesión de BD
3. Usar modelos de `app/models/entities.py` (Request, Category) para queries
4. Asegurar que SQLAlchemy mapee correctamente nombres legacy (español) ↔ código (inglés) usando `__tablename__`

**Archivos a verificar**:
- `agm-simulated-enviroment/backend/app/db/base.py`
- `agm-simulated-enviroment/backend/app/models/entities.py`

---

## FASE 4: Validaciones y Manejo de Errores

**Objetivo**: Estandarizar el manejo de errores y validaciones en todo el backend.

### 4.1. Manejo Centralizado de Errores

**Tareas**:
1. Crear excepciones personalizadas en `app/core/exceptions.py` (nuevo archivo):
   - `RequestNotFoundError`
   - `UnauthorizedError`
   - `ForbiddenError`
   - `ValidationError`
2. Crear exception handlers en `app/main.py`:
   - Mapear excepciones personalizadas a códigos HTTP apropiados:
     - `RequestNotFoundError` → `404 Not Found`
     - `UnauthorizedError` → `401 Unauthorized`
     - `ForbiddenError` → `403 Forbidden`
     - `ValidationError` → `422 Unprocessable Entity`
   - Retornar respuestas JSON consistentes con estructura estándar:
     ```json
     {
       "error": "error_code",
       "message": "Mensaje legible para el usuario",
       "detail": "Detalle técnico opcional",
       "timestamp": "2024-01-15T10:30:00Z"
     }
     ```
   - Crear función helper `create_error_response(error_code: str, message: str, detail: Optional[str] = None) -> dict`
   - Usar `datetime.utcnow().isoformat() + "Z"` para timestamp
3. Usar try/except en endpoints para capturar errores de BD y convertirlos a excepciones personalizadas

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/backend/app/core/exceptions.py` (nuevo)
- `agm-simulated-enviroment/backend/app/main.py`

### 4.2. Validación de Datos

**Tareas**:
1. Asegurar que todos los esquemas Pydantic tengan validaciones apropiadas:
   - Longitudes máximas de strings
   - Valores permitidos para enums
   - Validación de formatos (email, fechas, etc.)
2. Crear función `validate_state_transition()` en `app/services/validation_service.py` (nuevo archivo):
   - **Matriz de transiciones permitidas**:
     - Pendiente (1) → En Trámite (2) ✅ Permitido
     - Pendiente (1) → Solucionado (3) ✅ Permitido (cierre directo)
     - En Trámite (2) → Solucionado (3) ✅ Permitido
     - Solucionado (3) → Pendiente (1) ❌ No permitido
     - Solucionado (3) → En Trámite (2) ❌ No permitido
     - Cualquier estado → mismo estado ✅ Permitido (no-op)
   - Función: `validate_state_transition(current: int, new: int) -> bool`
   - Retornar `True` si transición permitida, `False` si no
   - Lanzar `ValueError` si estados no son válidos (1, 2, o 3)
3. Agregar validaciones de negocio en los routers:
   - Verificar que `codcategoria` existe en `HLP_CATEGORIAS` antes de crear solicitud (ya especificado en 3.2)
   - Validar transiciones de estado usando `validate_state_transition()` antes de actualizar `codestado`

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/backend/app/models/schemas.py`
- `agm-simulated-enviroment/backend/app/services/validation_service.py` (nuevo)
- `agm-simulated-enviroment/backend/app/routers/service_desk.py`

---

## FASE 5: Documentación y Testing

**Objetivo**: Asegurar que la API esté documentada y sea testeable.

### 5.1. Documentación Automática

**Tareas**:
1. Verificar que FastAPI genere documentación Swagger automáticamente en `/docs`
2. Agregar descripciones a todos los endpoints usando docstrings
3. Agregar ejemplos en los esquemas Pydantic usando `Field(..., example="...")`
4. Documentar códigos de respuesta HTTP en cada endpoint

**Archivos a modificar**:
- Todos los routers y schemas

### 5.2. Testing Básico

**Tareas**:
1. Crear estructura de tests en `tests/` (opcional para Fase 1):
   - `test_app_amerika.py`: Test de endpoint de Amerika
   - `test_app_domain.py`: Test de endpoint de Dominio
   - `test_service_desk.py`: Test de endpoints CRUD
   - `test_auth.py`: Test de autenticación JWT y API Key
2. Usar `httpx.AsyncClient` de FastAPI para tests de integración
3. Mockear validación JWT para tests de endpoints protegidos

**Archivos a crear** (opcional):
- `agm-simulated-enviroment/backend/tests/` (directorio nuevo)

---

## Notas de Implementación

### Mapeo de USUSOLICITA

**Decisión implementada**: `USUSOLICITA` se extrae del email del usuario autenticado.

**Estrategia**:
- Extraer la parte antes de `@` del email del JWT
- Ejemplo: `mzuloaga@aguasdemanizales.com.co` → `USUSOLICITA = "mzuloaga"`
- Ejemplo (PoC con Gmail): `mzuloaga@gmail.com` → `USUSOLICITA = "mzuloaga"`
- Validar formato de email antes de extraer username
- Si el username excede 25 caracteres (límite de `VARCHAR(25)`), lanzar error de validación (NO truncar para evitar colisiones)

**Implementación**:
```python
import re
from email_validator import validate_email, EmailNotValidError

def extract_username_from_email(email: str) -> str:
    """Extrae el username del email (parte antes de @)"""
    # Validar formato de email
    try:
        validate_email(email)
    except EmailNotValidError:
        raise ValueError("Formato de email inválido")
    
    # Extraer username
    username = email.split("@")[0]
    
    # Validar longitud (NO truncar)
    if len(username) > 25:
        raise ValueError(f"Username '{username}' excede 25 caracteres (límite: 25)")
    
    return username
```

### Estrategias de Autenticación: ANON_KEY vs SERVICE_ROLE_KEY

**IMPORTANTE**: El backend debe usar diferentes claves según el contexto de autenticación.

#### SUPABASE_ANON_KEY (Validación JWT de Usuarios)

**Cuándo usar**: Para validar tokens JWT emitidos por Supabase cuando usuarios autenticados acceden a endpoints protegidos.

**Propósito**:
- Validar que un token JWT fue firmado por Supabase
- Verificar que el token no ha expirado
- Extraer información del usuario (email, UUID) del token
- Respeta las políticas de Row Level Security (RLS)

**Uso en el backend**:
- Endpoints de Mesa de Servicio (`/api/requests/*`) que requieren autenticación de usuario
- Dependency `get_current_user()` que valida tokens de usuarios autenticados
- Todos los endpoints que necesitan identificar al usuario que hace la solicitud

**Ejemplo de uso**:
```python
from jose import jwt, JWTError
from app.core.config import settings

def verify_supabase_jwt(token: str) -> dict:
    """Valida token JWT usando SUPABASE_ANON_KEY"""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_ANON_KEY,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError:
        raise HTTPException(401, "Token inválido o expirado")
```

#### SUPABASE_SERVICE_ROLE_KEY (Operaciones del Sistema)

**Cuándo usar**: Para operaciones administrativas que requieren acceso completo, bypass de RLS, o acceso a todas las solicitudes sin restricciones de usuario.

**Propósito**:
- Bypass automático de Row Level Security (RLS)
- Acceso completo a todas las tablas y registros
- Operaciones administrativas del sistema
- Uso exclusivo del Agente AI

**Uso en el backend**:
- **NO se usa para validar tokens JWT de usuarios**
- Se reserva para el Agente AI (cuando se implemente) que necesita leer y actualizar todas las solicitudes
- Operaciones administrativas que requieren acceso completo

**IMPORTANTE - Seguridad**:
- ⚠️ **NUNCA exponer en el frontend**
- ⚠️ **NUNCA usar para validar tokens de usuarios**
- ⚠️ **Solo usar en el backend para operaciones del sistema**
- ⚠️ **El Agente AI usará esta clave para acceder a todas las solicitudes**

**Ejemplo de uso (futuro - Agente AI)**:
```python
# Esto NO es para validación JWT, sino para acceso directo a Supabase
from supabase import create_client
from app.core.config import settings

# Cliente de Supabase con SERVICE_ROLE_KEY (bypass RLS)
supabase_admin = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)

# El Agente AI puede leer todas las solicitudes sin restricciones
all_requests = supabase_admin.table("HLP_PETICIONES").select("*").execute()
```

**Resumen de decisión**:
- ✅ **Validación JWT de usuarios**: Usar `SUPABASE_ANON_KEY`
- ✅ **Operaciones del sistema/Agente AI**: Usar `SUPABASE_SERVICE_ROLE_KEY` (solo para acceso directo a Supabase, NO para validar JWT)

### Estructura de ai_classification_data

**Objetivo**: Definir la estructura JSON exacta del campo `ai_classification_data` que almacena información de clasificación del Agente AI.

**Estructura JSON**:
```json
{
  "app_type": "amerika",  // o "dominio"
  "confidence": 0.95,     // float entre 0.0 y 1.0
  "classification_timestamp": "2024-01-15T10:30:00Z",  // ISO8601
  "detected_actions": ["generate_password", "unlock_account"],  // Lista de acciones detectadas
  "raw_classification": "El usuario necesita cambiar su contraseña de Amerika y desbloquear su cuenta"  // Opcional
}
```

**Esquema Pydantic**:
```python
class AIClassificationData(BaseModel):
    app_type: Literal["amerika", "dominio"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    classification_timestamp: str  # ISO8601 format
    detected_actions: List[str]
    raw_classification: Optional[str] = None
```

**Campos**:
- `app_type`: Requerido. Tipo de aplicación detectada por el Agente AI
- `confidence`: Requerido. Nivel de confianza de la clasificación (0.0 = sin confianza, 1.0 = total confianza)
- `classification_timestamp`: Requerido. Timestamp ISO8601 de cuando se realizó la clasificación
- `detected_actions`: Requerido. Lista de acciones detectadas que el usuario necesita (ej: ["generate_password", "unlock_account"])
- `raw_classification`: Opcional. Texto original de la clasificación del Agente AI para auditoría

**Uso**: Este campo es actualizado por el Agente AI cuando procesa una solicitud. El backend debe validar la estructura antes de almacenar.

### Conversión de Estados

- **Backend**: Siempre retorna estados numéricos (1, 2, 3) en `RequestResponse`
- **Frontend**: Realiza conversión a texto ("Pendiente", "En Trámite", "Solucionado") para la UI
- **Helper function**: `estado_to_text()` puede estar en backend para uso interno, pero la conversión principal es responsabilidad del frontend

### Acceso a Supabase

- **SQLAlchemy**: Usado para todas las operaciones CRUD normales (acceso directo a PostgreSQL)
- **SDK de Supabase**: Solo necesario si se requiere funcionalidad específica de Supabase (ej: Realtime subscriptions, Storage). Para validación JWT, usar `python-jose` es suficiente.

### Seguridad

- **API Key**: Almacenar `API_SECRET_KEY` en variables de entorno, nunca en código
- **JWT**: 
  - Validar siempre la firma del token usando `SUPABASE_ANON_KEY` antes de confiar en su contenido
  - Validar expiración del token
  - Nunca usar `SUPABASE_SERVICE_ROLE_KEY` para validar tokens de usuarios
- **RLS**: Las políticas de Row Level Security en Supabase son la primera línea de defensa, pero el backend debe validar también que `USUSOLICITA` coincida con el usuario autenticado
- **SERVICE_ROLE_KEY**: 
  - Solo usar para operaciones del sistema (Agente AI)
  - Nunca exponer en frontend
  - Nunca usar para validar tokens JWT de usuarios

---

## Orden de Implementación Recomendado

1. **Fase 1** (Endpoints de Acción): Más simple, establece estructura base
2. **Fase 2** (Autenticación JWT): Necesaria para Fase 3
3. **Fase 3** (CRUD Mesa de Servicio): Depende de Fase 2
4. **Fase 4** (Validaciones y Errores): Mejora la robustez de todo el sistema
5. **Fase 5** (Documentación y Testing): Asegura calidad y mantenibilidad

---

## Referencias Cruzadas

- [Plan de Desarrollo Principal](./02_dev_plan.md) - Paso 2 (versión resumida)
- [Guía de Setup](./01_setup.md) - Configuración inicial del proyecto
- [Mapeo de Nomenclatura](../docs/NAMING_MAPPING.md) - Convenciones de nombres
- [Estructura del Backend](../docs/README.md#estructura-del-backend-unificado-agm-simulated-enviromentbackend) - Organización de archivos

