# Guía de Setup del Proyecto FastAPI

Esta guía te ayudará a crear el proyecto FastAPI básico para AGM Desk AI paso a paso.

**Referencia**: Para ver la estructura completa del backend, consulta la sección [Estructura del Backend Unificado](../docs/README.md#estructura-del-backend-unificado-agm-simulated-enviromentbackend) en el README principal.

## Objetivo

Crear un proyecto FastAPI básico con:

- Configuración de base de datos PostgreSQL (a través de Supabase)
- Endpoint de health
- Funcionamiento local

## PASO 1: Crear estructura básica del proyecto

Crea las estructuras de carpetas para los tres componentes principales del proyecto:

### Backend FastAPI

Crea la estructura de carpetas del backend FastAPI según la estructura definida en el [README](../docs/README.md#estructura-del-backend-unificado-agm-simulated-enviromentbackend).

**Referencia completa**: [Estructura del Backend Unificado](../docs/README.md#estructura-del-backend-unificado-agm-simulated-enviromentbackend)

### Frontend React

Crea la estructura de carpetas del frontend React según la estructura definida en el [README](../docs/README.md#estructura-del-frontend-agm-simulated-enviromentfrontend).

**Referencia completa**: [Estructura del Frontend](../docs/README.md#estructura-del-frontend-agm-simulated-enviromentfrontend)

### Agente AI

Crea la estructura de carpetas del agente AI según la estructura definida en el [README](../docs/README.md#estructura-del-agente-ai-agm-desk-ai).

**Referencia completa**: [Estructura del Agente AI](../docs/README.md#estructura-del-agente-ai-agm-desk-ai)

## PASO 2: Configurar dependencias

Crea `pyproject.toml` con estas dependencias mínimas:

```toml
[project]
name = "agm-desk-ai-backend"
version = "0.1.0"
description = "Backend FastAPI para AGM Desk AI"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "supabase>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.25.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Notas sobre las dependencias:**

- `fastapi`: Framework web moderno y rápido
- `uvicorn[standard]`: Servidor ASGI con soporte para HTTP/2 y WebSockets
- `sqlalchemy`: ORM para interactuar con PostgreSQL
- `asyncpg`: Driver asíncrono para PostgreSQL (mejor rendimiento que psycopg2-binary)
- `pydantic` y `pydantic-settings`: Validación de datos y configuración desde variables de entorno
- `python-dotenv`: Carga de variables de entorno desde archivo `.env`
- `supabase`: Cliente oficial de Python para interactuar con Supabase
- `python-jose[cryptography]`: Validación de tokens JWT de Supabase
- `httpx`: Cliente HTTP asíncrono (requerido por Supabase)

## PASO 3: Crear configuración de la aplicación

En app/core/config.py:

- Crear clase Settings usando pydantic-settings
- Incluir PROJECT_NAME, VERSION
- Incluir DATABASE_URL para PostgreSQL
- Configurar para leer variables de entorno

## PASO 4: Crear aplicación FastAPI básica

En app/main.py:

- Crear instancia FastAPI con título y versión desde config
- Endpoint GET "/" que retorne mensaje de bienvenida
- Endpoint GET "/health" que retorne status, service name y version
- NO crear otros endpoints aún

## PASO 5: Verificar funcionamiento local

Instalar dependencias y ejecutar:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Verificar que respondan:

- <http://localhost:8000/> (mensaje bienvenida)
- <http://localhost:8000/health> (status ok)
- <http://localhost:8000/docs> (documentación automática)

## PASO 6: Configurar conexión a base de datos

En app/db/base.py:

- Importar DATABASE_URL desde app.core.config
- Configurar SQLAlchemy engine asíncrono usando create_async_engine con DATABASE_URL
- Crear AsyncSessionLocal para sesiones de DB asíncronas
- Crear Base declarativa para futuros modelos
- Función get_db() async para dependency injection en FastAPI
