# Guía Rápida: Ejecutar en Local

Esta guía te permite ejecutar y probar los componentes implementados del proyecto AGM Desk AI en tu máquina local.

> **Método Recomendado**: Usa **Supabase** como base de datos. No requiere Docker y es más simple de configurar. Ver detalles en `agm-simulated-enviroment/backend/docs/DATABASE_SETUP.md`

---

## 🚀 Inicio Rápido (Backend)

### 1. Configurar Base de Datos

**Opción Recomendada: Supabase**

1. Crea un proyecto en Supabase (https://supabase.com)
2. Obtén la connection string desde Settings > Database
3. Configura las variables de entorno (ver paso 2)

**Opción Opcional: PostgreSQL Local (solo si no puedes usar Supabase)**

```bash
cd agm-simulated-enviroment/backend

# Iniciar PostgreSQL con Docker
docker-compose up -d

# Verificar que está corriendo
docker ps | grep postgres
```

### 2. Configurar Variables de Entorno

Crear archivo `.env` en `agm-simulated-enviroment/backend/`:

**Para Supabase (Recomendado):**

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here
API_SECRET_KEY=mi-clave-secreta-123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0
```

**Para PostgreSQL Local (Opcional):**

```env
DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db
API_SECRET_KEY=mi-clave-secreta-123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0
```

### 3. Instalar Dependencias y Ejecutar Migraciones

```bash
# Instalar dependencias (con uv)
uv sync

# O con pip
pip install -e .

# Ejecutar migraciones
uv run alembic upgrade head
# o
alembic upgrade head
```

### 4. Iniciar el Servidor

```bash
# Con uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O con pip
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verificar que Funciona

- **API**: http://localhost:8000/
- **Health**: http://localhost:8000/health
- **Documentación**: http://localhost:8000/docs

---

## ✅ Endpoints Disponibles para Probar

### Endpoints de Acción (requieren API Key)

**Amerika - Generar Contraseña**:

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mi-clave-secreta-123" \
  -d '{
    "user_id": "test_user",
    "action_type": "generate_password"
  }'
```

**Dominio - Buscar Usuario**:

```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mi-clave-secreta-123" \
  -d '{
    "user_id": "test_user",
    "action_type": "find_user",
    "user_name": "mzuloaga"
  }'
```

**Dominio - Cambiar Contraseña**:

```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mi-clave-secreta-123" \
  -d '{
    "user_id": "test_user",
    "action_type": "change_password"
  }'
```

### Endpoints de Mesa de Servicio (requieren JWT de Supabase)

**Nota**: Para probar estos endpoints, necesitas:
1. Configurar Supabase (o usar un token JWT de prueba)
2. Obtener un token JWT válido
3. Usar el token en el header `Authorization: Bearer <token>`

**Crear Solicitud**:

```bash
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_JWT_TOKEN_AQUI" \
  -d '{
    "codcategoria": 300,
    "description": "Necesito cambiar mi contraseña de dominio"
  }'
```

**Listar Solicitudes**:

```bash
curl -X GET http://localhost:8000/api/requests \
  -H "Authorization: Bearer TU_JWT_TOKEN_AQUI"
```

---

## 📊 Estado de Implementación

### ✅ Completamente Implementado

- **Backend FastAPI**: 100% funcional
  - Endpoints de acción (Amerika y Dominio)
  - Endpoints CRUD de Mesa de Servicio
  - Autenticación JWT
  - Validaciones y manejo de errores
  - Generación de contraseñas seguras

- **Base de Datos**: 100% configurada
  - Modelos SQLAlchemy
  - Migraciones Alembic
  - Scripts de setup

### ⚠️ Parcialmente Implementado

- **Frontend React**: Estructura creada, necesita implementación completa
- **Agente AI**: Estructura creada, necesita implementación completa

---

## 🔧 Comandos Útiles

### Base de Datos

```bash
# Ver logs de PostgreSQL
docker-compose logs -f postgres

# Conectar a PostgreSQL
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db

# Ver tablas
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "\dt"

# Ver categorías
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "SELECT * FROM HLP_CATEGORIAS;"

# Detener PostgreSQL
docker-compose down

# Detener y eliminar datos
docker-compose down -v
```

### Backend

```bash
# Verificar migraciones
uv run alembic current

# Crear nueva migración
uv run alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
uv run alembic upgrade head

# Revertir última migración
uv run alembic downgrade -1
```

---

## 🐛 Solución de Problemas

### El servidor no inicia

1. Verifica que PostgreSQL esté corriendo: `docker ps | grep postgres`
2. Verifica el archivo `.env` existe y tiene las variables correctas
3. Verifica que las migraciones se ejecutaron: `alembic current`

### Error 401 en endpoints de acción

- Verifica que `API_SECRET_KEY` en `.env` coincida con el header `X-API-Key`
- Verifica que el header esté presente en la petición

### Error de conexión a base de datos

- Verifica que PostgreSQL esté corriendo
- Verifica `DATABASE_URL` en `.env`
- Prueba conexión manual: `docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db`

---

## 📚 Documentación Completa

Para más detalles, consulta:
- [Estado de Implementación Detallado](./ESTADO_IMPLEMENTACION.md)
- [Guía de Setup de Base de Datos](../agm-simulated-enviroment/backend/docs/DATABASE_SETUP.md)
- [Especificación del Backend](../specs/03_backend_detailed.md)

