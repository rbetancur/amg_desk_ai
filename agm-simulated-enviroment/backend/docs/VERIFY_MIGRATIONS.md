# Cómo Verificar si las Migraciones se Aplicaron

## Método 1: Dashboard de Supabase (Más Simple) ⭐ RECOMENDADO

1. Ve al Dashboard de Supabase:
   https://supabase.com/dashboard/project/jqzuacudoegneaueroan

2. Ve a **Database** > **Tables**

3. Deberías ver estas tablas:
   - ✅ `HLP_CATEGORIAS`
   - ✅ `HLP_PETICIONES`
   - ✅ `alembic_version` (tabla interna de Alembic)

4. Haz clic en `HLP_CATEGORIAS` y verifica que tenga 2 registros:
   - CODCATEGORIA: 300, CATEGORIA: "Cambio de Contraseña Cuenta Dominio"
   - CODCATEGORIA: 400, CATEGORIA: "Cambio de Contraseña Amerika"

## Método 2: SQL Editor en Supabase

1. Ve a **SQL Editor** en el Dashboard
2. Ejecuta esta consulta:

```sql
-- Verificar tablas creadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('HLP_CATEGORIAS', 'HLP_PETICIONES', 'alembic_version')
ORDER BY table_name;

-- Verificar versión de Alembic
SELECT version_num FROM alembic_version;

-- Verificar datos seed
SELECT * FROM HLP_CATEGORIAS;

-- Verificar estructura de HLP_PETICIONES
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'HLP_PETICIONES'
ORDER BY ordinal_position;
```

## Método 3: Verificación con Alembic (Requiere dependencias instaladas)

```bash
cd agm-simulated-enviroment/backend
source .venv/bin/activate

# Ver estado actual de migraciones
alembic current

# Ver historial de migraciones
alembic history
```

**Resultado esperado:**
```
001_initial (head)
```

## Método 4: Verificación con Python (Requiere dependencias instaladas)

```bash
cd agm-simulated-enviroment/backend
source .venv/bin/activate
python scripts/verify-tables.py
```

## ¿Qué buscar?

### ✅ Migraciones Aplicadas Correctamente

Si las migraciones se aplicaron, deberías ver:

1. **Tabla `alembic_version`** existe con versión `001_initial`
2. **Tabla `HLP_CATEGORIAS`** existe con 2 registros
3. **Tabla `HLP_PETICIONES`** existe con todas las columnas:
   - CODPETICIONES (PK)
   - CODCATEGORIA (FK)
   - CODESTADO, CODPRIORIDAD, etc.
   - AI_CLASSIFICATION_DATA (JSONB)

### ❌ Migraciones NO Aplicadas

Si las migraciones NO se aplicaron:

1. No verás las tablas en el Dashboard
2. La tabla `alembic_version` no existirá
3. Necesitarás ejecutar: `alembic upgrade head`

## Solución Rápida

Si las migraciones NO se aplicaron:

```bash
cd agm-simulated-enviroment/backend

# Instalar dependencias primero (si no están instaladas)
# Opción 1: Con pip
source .venv/bin/activate
pip install alembic sqlalchemy psycopg2-binary

# Opción 2: Con uv (si está disponible)
uv sync

# Ejecutar migraciones
alembic upgrade head
```

## Verificación Rápida desde el Dashboard

La forma más rápida es:

1. Abre: https://supabase.com/dashboard/project/jqzuacudoegneaueroan/database/tables
2. Busca las tablas `HLP_CATEGORIAS` y `HLP_PETICIONES`
3. Si existen → ✅ Migraciones aplicadas
4. Si NO existen → ❌ Ejecuta `alembic upgrade head`

