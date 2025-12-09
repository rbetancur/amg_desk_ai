# Guía: Conexión Funcional a Supabase y Ejecución del Proyecto

## Paso 1: Verificar y Configurar DATABASE_URL

### Opción A: Usar Connection Pooling (Recomendado para producción)

1. Ve a **Supabase Dashboard** > **Settings** > **Database**
2. En la sección **Connection String**, selecciona:
   - **Connection Pooling**: ✅ Activado
   - **Mode**: **Transaction mode**
3. Copia la connection string. Debería verse así:
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```
   o
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### Opción B: Usar Direct Connection (Si Pooling falla)

Si tienes problemas de conexión con pooling, usa la conexión directa:

1. Ve a **Supabase Dashboard** > **Settings** > **Database**
2. En la sección **Connection String**, selecciona:
   - **Connection Pooling**: ❌ Desactivado
   - **Mode**: **Direct connection**
3. Copia la connection string. Debería verse así:
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

### Actualizar .env

Edita el archivo `.env` en `agm-simulated-enviroment/backend/.env`:

```env
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:5432/postgres
```

**Importante**: Reemplaza `[PROJECT-REF]`, `[PASSWORD]`, y `[HOST]` con los valores reales de tu proyecto.

## Paso 2: Verificar Credenciales en .env

Asegúrate de que tu archivo `.env` tenga todas las variables requeridas:

```env
# Connection String de Supabase (REQUERIDA)
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:5432/postgres

# API Keys de Supabase (REQUERIDAS)
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here

# API Key para endpoints de acción
API_SECRET_KEY=dev-api-secret-key-12345

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Configuración de la aplicación
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0

# Redis (Opcional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Paso 3: Verificar que el Proyecto de Supabase esté Activo

1. Ve al **Supabase Dashboard**
2. Verifica que el proyecto esté **activo** (no pausado)
3. Verifica que todos los servicios estén **Healthy**:
   - Database: ✅ Healthy
   - PostgREST: ✅ Healthy
   - Auth: ✅ Healthy
   - Realtime: ✅ Healthy
   - Storage: ✅ Healthy

## Paso 4: Instalar Dependencias

```bash
cd agm-simulated-enviroment/backend

# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings python-dotenv supabase 'python-jose[cryptography]' email-validator httpx alembic redis psycopg2-binary
```

O si usas `uv`:

```bash
cd agm-simulated-enviroment/backend
uv sync
```

## Paso 5: Ejecutar Migraciones

```bash
cd agm-simulated-enviroment/backend

# Activar entorno virtual si no está activo
source .venv/bin/activate

# Ejecutar migraciones
alembic upgrade head
```

**Resultado esperado**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial migration
```

Si las migraciones ya están aplicadas, verás:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

## Paso 6: Verificar Estado de Migraciones

```bash
cd agm-simulated-enviroment/backend
source .venv/bin/activate

# Ver migración actual
alembic current
```

**Resultado esperado**:
```
001_initial (head)
```

## Paso 7: Verificar Conexión

```bash
cd agm-simulated-enviroment/backend

# Usar el script de verificación
./scripts/check-db.sh
```

O verificar manualmente:

```bash
# Verificar conexión usando Python
source .venv/bin/activate
python3 -c "
import asyncio
from app.db.base import engine
from sqlalchemy import text

async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('✅ Conexión exitosa')

asyncio.run(test())
"
```

## Paso 8: Ejecutar el Backend

```bash
cd agm-simulated-enviroment/backend

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Resultado esperado**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Paso 9: Verificar Health Check

En otra terminal:

```bash
curl http://localhost:8000/health
```

**Resultado esperado**:
```json
{
  "status": "ok",
  "service": "AGM Desk AI Backend",
  "version": "0.1.0",
  "database": {
    "type": "supabase",
    "status": "connected"
  }
}
```

## Troubleshooting

### Error: "Connection refused" o "Connect call failed"

**Causas posibles**:
1. El proyecto de Supabase está pausado
2. Problema con IPv6 (el sistema intenta usar IPv6 y falla)
3. La `DATABASE_URL` usa connection pooling y hay problemas de red

**Soluciones**:

1. **Verificar que el proyecto esté activo**:
   - Ve al Dashboard de Supabase
   - Si está pausado, reactívalo

2. **Probar con Direct Connection**:
   - Obtén la connection string de "Direct connection" (sin pooling)
   - Actualiza `DATABASE_URL` en `.env`
   - Intenta conectarte de nuevo

3. **Verificar conectividad de red**:
   ```bash
   # Probar conectividad básica
   ping db.jqzuacudoegneaueroan.supabase.co
   
   # Probar conexión PostgreSQL
   psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" -c "SELECT 1"
   ```

4. **Forzar IPv4** (si el problema es IPv6):
   - En algunos casos, puedes agregar `?options=-c%20ip_family=ipv4` a la URL
   - O configurar tu sistema para preferir IPv4

### Error: "ModuleNotFoundError: No module named 'psycopg2'"

**Solución**:
```bash
source .venv/bin/activate
pip install psycopg2-binary
```

### Error: "alembic: command not found"

**Solución**:
```bash
source .venv/bin/activate
pip install alembic
```

O usa:
```bash
.venv/bin/alembic upgrade head
```

### Error: "DATABASE_URL no puede apuntar a localhost"

**Solución**:
- Verifica que `DATABASE_URL` en `.env` apunte a Supabase
- No debe contener `localhost` o `127.0.0.1`
- Debe contener `supabase` en el hostname

### Error: "SUPABASE_URL, SUPABASE_ANON_KEY, o SUPABASE_JWT_SECRET no configuradas"

**Solución**:
- Verifica que todas las variables estén en `.env`
- Obtén las variables desde: **Supabase Dashboard** > **Settings** > **API**

## Verificación Final

Una vez que todo esté configurado, deberías poder:

1. ✅ Ejecutar migraciones sin errores
2. ✅ Verificar conexión con `./scripts/check-db.sh`
3. ✅ Iniciar el backend sin errores
4. ✅ Acceder a `http://localhost:8000/health` y ver `"status": "ok"`
5. ✅ Acceder a `http://localhost:8000/` y ver el mensaje de bienvenida

## Próximos Pasos

Una vez que la conexión funcione:

1. **Configurar RLS** (Row Level Security):
   - Ve a **Supabase Dashboard** > **Authentication** > **Policies**
   - Configura las políticas para `HLP_PETICIONES`
   - Ver `docs/DATABASE_SETUP.md` para instrucciones detalladas

2. **Habilitar Realtime**:
   - Ve a **Database** > **Replication**
   - Habilita Realtime para `HLP_PETICIONES`
   - Habilita eventos INSERT y UPDATE

3. **Ejecutar el Frontend**:
   ```bash
   cd agm-simulated-enviroment/frontend
   npm install
   npm run dev
   ```

