# Guía de Configuración de Base de Datos

Esta guía explica cómo configurar Supabase para el proyecto AGM Desk AI.

**IMPORTANTE**: Este proyecto **solo soporta Supabase** como base de datos. No se soporta PostgreSQL local.

## Tabla de Contenidos

- [Supabase](#supabase)
- [Migraciones](#migraciones)
- [Verificación](#verificación)
- [Redis (Opcional)](#redis-opcional)
- [Troubleshooting](#troubleshooting)

---

## Supabase

### Requisitos

- Cuenta en Supabase (https://supabase.com)
- Proyecto creado en Supabase

### Configuración Paso a Paso

#### 1. Crear Proyecto en Supabase

1. Ve a https://supabase.com y crea una cuenta o inicia sesión
2. Haz clic en "New Project"
3. Completa el formulario:
   - **Name**: Nombre del proyecto (ej: `agm-desk-ai`)
   - **Database Password**: ⚠️ **Guarda esta contraseña**, la necesitarás para la connection string
   - **Region**: Elige la región más cercana
4. Haz clic en "Create new project"
5. Espera a que el proyecto se cree (puede tomar 1-2 minutos)

#### 2. Obtener Connection String

1. En el Dashboard de Supabase, ve a **Project Settings** (ícono de engranaje en la barra lateral)
2. Selecciona **Database** en el menú izquierdo
3. Desplázate hasta la sección **Connection String**
4. Selecciona **Connection Pooling** y elige **Transaction mode**
5. Copia la connection string. Tendrá el formato:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```
6. Reemplaza `[YOUR-PASSWORD]` con la contraseña de la base de datos que guardaste en el paso 1

#### 3. Obtener API Keys

1. En **Project Settings** > **API**
2. Copia los siguientes valores:
   - **Project URL**: `https://[PROJECT-REF].supabase.co`
   - **anon public key**: Empieza con `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **JWT Secret**: En la misma página, busca "JWT Secret" (necesario para validación de tokens)
   - **service_role key**: ⚠️ **Mantén esta clave segura**, permite bypass de RLS

#### 4. Configurar archivo .env

Crea un archivo `.env` en `agm-simulated-enviroment/backend/` con el siguiente contenido:

```env
# Connection String de Supabase (REQUERIDA)
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres

# API Keys de Supabase (REQUERIDAS)
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here

# SUPABASE_SERVICE_ROLE_KEY (Opcional, requerida para Agente AI)
SUPABASE_SERVICE_ROLE_KEY=

# API Key para endpoints de acción
API_SECRET_KEY=dev-api-secret-key-12345

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Configuración de la aplicación
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0

# Redis (Opcional - para cache)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Reemplaza los valores entre corchetes con tus credenciales reales.

**Usando el Script de Configuración**:

Puedes usar el script automatizado que te guiará paso a paso:

```bash
./scripts/setup-db.sh
```

Este script:
- Verifica que tengas las credenciales de Supabase
- Crea el archivo `.env` si no existe
- Valida la configuración
- Ejecuta las migraciones automáticamente

#### 5. Ejecutar Migraciones

```bash
# Activar entorno virtual si es necesario
source .venv/bin/activate

# Ejecutar migraciones
alembic upgrade head
```

Esto creará las tablas `HLP_CATEGORIAS` y `HLP_PETICIONES` en Supabase.

#### 6. Habilitar Realtime para HLP_PETICIONES

El Realtime es necesario para que el Agente AI detecte nuevas solicitudes en tiempo real.

1. En el Dashboard de Supabase, ve a **Database** > **Replication**
2. Busca la tabla `HLP_PETICIONES` en la lista
3. Activa el toggle de **Realtime** para `HLP_PETICIONES`
4. Asegúrate de que los eventos **INSERT** y **UPDATE** estén habilitados

#### 7. Configurar Row Level Security (RLS)

RLS asegura que los usuarios solo puedan ver y editar sus propias solicitudes.

##### Habilitar RLS en la tabla

1. Ve a **Database** > **Tables**
2. Selecciona la tabla `HLP_PETICIONES`
3. Haz clic en el ícono de candado (🔒) junto al nombre de la tabla
4. Activa **Enable Row Level Security**

##### Crear Función SQL Helper

**IMPORTANTE**: Para la PoC, `USUSOLICITA` contiene el username extraído del email del usuario (parte antes de `@`), no el UUID. Por ejemplo: `mzuloaga@aguasdemanizales.com.co` → `USUSOLICITA = "mzuloaga"`.

Primero, crea una función SQL helper que extraiga el username del email del usuario autenticado:

1. Ve a **SQL Editor** en el Dashboard de Supabase
2. Ejecuta el siguiente SQL:

```sql
CREATE OR REPLACE FUNCTION get_username_from_auth_user()
RETURNS TEXT AS $$
  SELECT SUBSTRING(
    (SELECT email FROM auth.users WHERE id = auth.uid()) 
    FROM '^([^@]+)'
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;
```

**Explicación**:
- `SECURITY DEFINER`: Permite que la función acceda a `auth.users` incluso cuando es llamada desde políticas RLS
- `STABLE`: Indica que la función retorna el mismo resultado para la misma entrada dentro de una transacción
- La función extrae la parte antes de `@` del email del usuario autenticado

**Verificar que la función se creó correctamente**:
```sql
-- Probar la función (debe ejecutarse como usuario autenticado)
SELECT get_username_from_auth_user();
```

##### Crear Políticas RLS

Ve a **Authentication** > **Policies** y crea las siguientes políticas:

**⚠️ Si ya tienes políticas RLS creadas con el formato antiguo** (`auth.uid()::text = USUSOLICITA`), elimínalas primero desde el Dashboard antes de crear las nuevas.

**Política 1: Usuarios pueden ver sus propias solicitudes**

- **Name**: `Users can view own requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `SELECT`
- **Policy definition**: Usa el editor SQL y pega:

```sql
(
  get_username_from_auth_user() = "USUSOLICITA"
)
```

**Política 2: Usuarios pueden crear solicitudes**

- **Name**: `Users can create requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `INSERT`
- **Policy definition**:

```sql
(
  get_username_from_auth_user() = "USUSOLICITA"
)
```

**Política 3: Usuarios pueden actualizar sus propias solicitudes (opcional)**

- **Name**: `Users can update own requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `UPDATE`
- **Policy definition**:

```sql
(
  get_username_from_auth_user() = "USUSOLICITA"
)
```

**Notas importantes**:
- **Mapeo de USUSOLICITA**: `USUSOLICITA` contiene el username extraído del email (ej: `mzuloaga` de `mzuloaga@aguasdemanizales.com.co`). El backend extrae automáticamente este valor del JWT del usuario autenticado.
- **Validación de longitud**: El campo `USUSOLICITA` es `VARCHAR(25)`. El backend debe validar que el username no exceda 25 caracteres antes de insertar.
- **Service Role Key**: El `SUPABASE_SERVICE_ROLE_KEY` permite bypass automático de RLS. El Agente AI usará esta clave para leer y actualizar todas las solicitudes sin restricciones.
- **Rendimiento**: Las políticas RLS consultan `auth.users` en cada operación. Este overhead es aceptable para la PoC, pero puede optimizarse en producción usando metadata del usuario.

##### Alternativa: Usar Script SQL Completo

Puedes usar el script SQL completo que incluye la función y todas las políticas. Ver sección [Script SQL para Configurar RLS](#script-sql-para-configurar-rls) más abajo.

#### 7.1. Paso a Paso para Actualizar Políticas RLS Existentes

Si ya tienes políticas RLS configuradas con el formato antiguo (usando `auth.uid()::text`), sigue estos pasos para actualizarlas:

**Paso 1: Crear la función SQL helper**

1. Ve a **SQL Editor** en el Dashboard de Supabase
2. Ejecuta el siguiente SQL:

```sql
CREATE OR REPLACE FUNCTION get_username_from_auth_user()
RETURNS TEXT AS $$
  SELECT SUBSTRING(
    (SELECT email FROM auth.users WHERE id = auth.uid()) 
    FROM '^([^@]+)'
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;
```

3. Verifica que la función se creó correctamente ejecutando:
```sql
SELECT get_username_from_auth_user();
```

**Paso 2: Eliminar políticas RLS antiguas**

1. Ve a **Authentication** > **Policies** en el Dashboard
2. Busca las políticas para la tabla `HLP_PETICIONES`:
   - `Users can view own requests` (SELECT)
   - `Users can create requests` (INSERT)
   - `Users can update own requests` (UPDATE) - si existe
3. Elimina cada política haciendo clic en el ícono de eliminar (🗑️)

**Paso 3: Crear nuevas políticas RLS**

Sigue las instrucciones en la sección [Crear Políticas RLS](#crear-políticas-rls) más arriba, o usa el script SQL completo de la sección siguiente.

**Paso 4: Verificar las políticas**

1. En **Authentication** > **Policies**, verifica que las nuevas políticas estén creadas
2. Verifica que usen `get_username_from_auth_user() = "USUSOLICITA"` en lugar de `auth.uid()::text = "USUSOLICITA"`

#### 7.2. Script SQL para Configurar RLS

Puedes ejecutar este script SQL completo en el **SQL Editor** de Supabase para configurar todo de una vez:

```sql
-- ============================================
-- Script: Configurar RLS para USUSOLICITA (Username extraído del email)
-- ============================================
-- Este script crea la función helper y las políticas RLS necesarias
-- para que los usuarios solo puedan acceder a sus propias solicitudes
-- basándose en el username extraído de su email.
--
-- IMPORTANTE: Ejecuta este script DESPUÉS de crear las tablas con las migraciones
-- ============================================

-- Paso 1: Crear función helper para extraer username del email
CREATE OR REPLACE FUNCTION get_username_from_auth_user()
RETURNS TEXT AS $$
  SELECT SUBSTRING(
    (SELECT email FROM auth.users WHERE id = auth.uid()) 
    FROM '^([^@]+)'
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Paso 2: Eliminar políticas antiguas si existen (opcional, comentar si no las tienes)
-- Descomenta las siguientes líneas si necesitas eliminar políticas antiguas:
-- DROP POLICY IF EXISTS "Users can view own requests" ON "HLP_PETICIONES";
-- DROP POLICY IF EXISTS "Users can create requests" ON "HLP_PETICIONES";
-- DROP POLICY IF EXISTS "Users can update own requests" ON "HLP_PETICIONES";

-- Paso 3: Crear política para SELECT (ver solicitudes)
CREATE POLICY "Users can view own requests"
ON "HLP_PETICIONES"
FOR SELECT
USING (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- Paso 4: Crear política para INSERT (crear solicitudes)
CREATE POLICY "Users can create requests"
ON "HLP_PETICIONES"
FOR INSERT
WITH CHECK (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- Paso 5: Crear política para UPDATE (actualizar solicitudes)
CREATE POLICY "Users can update own requests"
ON "HLP_PETICIONES"
FOR UPDATE
USING (
  get_username_from_auth_user() = "USUSOLICITA"
)
WITH CHECK (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- Verificar que todo se creó correctamente
SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual
FROM pg_policies
WHERE tablename = 'HLP_PETICIONES'
ORDER BY policyname;
```

**Instrucciones de uso**:

1. Copia el script completo
2. Ve a **SQL Editor** en el Dashboard de Supabase
3. Pega el script en el editor
4. Si ya tienes políticas antiguas, descomenta las líneas del Paso 2 antes de ejecutar
5. Ejecuta el script (Run o F5)
6. Verifica que no haya errores
7. Verifica que las políticas se crearon correctamente ejecutando la consulta de verificación al final

**Nota**: Este script también está disponible en `agm-simulated-enviroment/backend/scripts/setup-rls-username.sql`

#### 8. Configurar Autenticación

1. En el Dashboard de Supabase, ve a **Authentication** (en el menú lateral izquierdo)
2. En la sección **CONFIGURATION**, haz clic en **Sign In / Providers**
3. En la lista de proveedores, busca y haz clic en **Email** para abrir su configuración
4. Dentro de la configuración del proveedor **Email**, encontrarás las siguientes opciones:

   **Opciones de Seguridad:**
   
   - **Enable Email provider**: 
     - Toggle que habilita/deshabilita el proveedor Email
     - Debe estar **ON** (verde) para usar autenticación por email
   
   - **Secure email change**: 
     - Toggle que requiere confirmación en ambos emails (actual y nuevo) cuando un usuario cambia su dirección de correo
     - **Recomendado para producción**: Actívalo (ON) para mayor seguridad
   
   - **Secure password change**: 
     - Toggle que requiere que el usuario haya iniciado sesión recientemente (últimas 24 horas) para cambiar su contraseña
     - Opcional: Actívalo si quieres mayor seguridad
   
   - **Prevent use of leaked passwords**: 
     - Toggle que rechaza contraseñas conocidas o fáciles de adivinar
     - Solo disponible en planes Pro y superiores
     - Opcional: Actívalo si tienes un plan Pro
   
   **Configuración de Contraseñas:**
   
   - **Minimum password length**: 
     - Valor por defecto: 6 caracteres
     - **Configuración según política del proyecto**: **10 caracteres**
     - Justificación: 
       - Cuentas de Dominio: Requieren mínimo 10 caracteres
       - Aplicación Amerika: Requiere mínimo 10 caracteres, máximo 25
       - Se configura el mínimo común más restrictivo: **10 caracteres**
   
   - **Password Requirements**: 
     - Dropdown para configurar requisitos de caracteres (mayúsculas, minúsculas, números, símbolos)
     - Por defecto: "No required characters"
     - **Configuración según política del proyecto**: 
       - **Seleccionar**: **"Lowercase, uppercase letters, digits and symbols (recommended)"**
       - Justificación (política más restrictiva que cumple con ambas):
         - **Cuentas de Dominio**: Requieren letras mayúsculas, minúsculas, números y/o símbolos
         - **Aplicación Amerika**: Requiere contraseñas alfanuméricas (letras y números)
         - **Configuración elegida**: Incluye mayúsculas, minúsculas, números Y símbolos
         - Esta configuración es la más completa y asegura que las contraseñas cumplan con AMBAS políticas simultáneamente
         - Nota: Los símbolos son opcionales en Dominio ("y/o"), pero al incluirlos garantizamos compatibilidad total
   
   **Configuración de OTP (One-Time Password):**
   
   - **Email OTP Expiration**: 
     - Duración antes de que un OTP/link de email expire
     - Valor por defecto: 3600 segundos (1 hora)
   
   - **Email OTP Length**: 
     - Número de dígitos en el OTP de email
     - Valor por defecto: 8 dígitos

5. **Configuración recomendada según política del proyecto:**
   
   **Opciones de Seguridad:**
   - ✅ **Enable Email provider**: ON
   - ✅ **Secure email change**: ON (ya lo tienes activado)
   - ⚠️ **Secure password change**: ON (recomendado para mayor seguridad)
   - ⚠️ **Prevent use of leaked passwords**: ON (si tienes plan Pro, recomendado)
   
   **Configuración de Contraseñas (según política del proyecto - configuración más restrictiva):**
   - ✅ **Minimum password length**: **10 caracteres**
     - Justificación: 
       - Cuentas de Dominio: Requieren mínimo 10 caracteres
       - Aplicación Amerika: Requieren mínimo 10 caracteres, máximo 25
       - Se configura el mínimo común más restrictivo: **10 caracteres**
   
   - ✅ **Password Requirements**: **"Lowercase, uppercase letters, digits and symbols (recommended)"**
     - Justificación (política más restrictiva que cumple con ambas):
       - **Cuentas de Dominio**: Requieren letras mayúsculas, minúsculas, números y/o símbolos
       - **Aplicación Amerika**: Requieren contraseñas alfanuméricas (letras y números)
       - **Configuración elegida**: Incluye mayúsculas, minúsculas, números Y símbolos
       - Esta es la configuración más completa que asegura compatibilidad con AMBAS políticas
       - Principio: "Ir por lo más restrictivo, no por lo menos" - garantiza que cualquier contraseña válida en Supabase cumplirá con los requisitos de ambas aplicaciones

6. Haz clic en **Save** para guardar los cambios

**Nota sobre "Confirm email"**: En versiones recientes de Supabase, la confirmación de email se maneja automáticamente a través del sistema de OTP (One-Time Password). Los usuarios recibirán un email con un código OTP o un link de confirmación cuando se registren, según la configuración de tu aplicación.

#### 9. Verificar Configuración

Usa el script de verificación:

```bash
./scripts/check-db.sh
```

O verifica manualmente:

```bash
# Verificar migraciones aplicadas
alembic current

# Verificar en Dashboard
# Database > Tables > Verificar que HLP_CATEGORIAS y HLP_PETICIONES existan
```

#### 9.1. Validar Políticas RLS

Después de configurar las políticas RLS, valida que funcionen correctamente:

**Opción 1: Usar script de prueba SQL**

1. Ve a **SQL Editor** en el Dashboard de Supabase
2. Abre el archivo `agm-simulated-enviroment/backend/scripts/test-rls-username.sql`
3. Ejecuta las pruebas 1-5 (no requieren autenticación):
   - Verificar que la función existe
   - Verificar estructura de la función
   - Verificar que las políticas existen
   - Verificar contenido de las políticas
   - Verificar que RLS está habilitado

**Opción 2: Validación manual**

Ejecuta estas consultas en el **SQL Editor**:

```sql
-- Verificar función
SELECT routine_name, routine_type 
FROM information_schema.routines
WHERE routine_name = 'get_username_from_auth_user';

-- Verificar políticas
SELECT policyname, cmd as operation
FROM pg_policies
WHERE tablename = 'HLP_PETICIONES';

-- Verificar RLS habilitado
SELECT tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'HLP_PETICIONES';
```

**Pruebas con usuarios autenticados** (requieren frontend/backend):

Las pruebas 6-9 del script `test-rls-username.sql` requieren usuarios autenticados y deben ejecutarse durante el desarrollo del frontend y backend:

- **Prueba 6**: Verificar que la función retorna el username correcto del usuario autenticado
- **Prueba 7**: Verificar que `SUPABASE_SERVICE_ROLE_KEY` bypass RLS
- **Prueba 8**: Validar edge cases (emails largos, caracteres especiales, etc.)
- **Prueba 9**: Validar que las políticas RLS funcionan correctamente (usuarios solo ven sus propias solicitudes)

Ver el archivo `agm-simulated-enviroment/backend/scripts/test-rls-username.sql` para detalles completos de las pruebas.

---

## Migraciones

### Ejecutar Migraciones

```bash
# Activar entorno virtual si es necesario
source .venv/bin/activate

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Aplicar la siguiente migración
alembic upgrade +1

# Revertir la última migración
alembic downgrade -1

# Revertir todas las migraciones
alembic downgrade base
```

### Verificar Estado de Migraciones

```bash
# Ver migración actual
alembic current

# Ver historial de migraciones
alembic history

# Ver migraciones pendientes
alembic heads
```

### Crear Nueva Migración

```bash
# Generar migración automática basada en cambios en modelos
alembic revision --autogenerate -m "Descripción de la migración"

# Crear migración vacía
alembic revision -m "Descripción de la migración"
```

---

## Verificación

### Script de Verificación Automática

```bash
./scripts/check-db.sh
```

Este script verifica:
- Configuración de `.env`
- Variables de Supabase requeridas
- Conexión a Supabase
- Estado de las migraciones

### Verificación Manual

```bash
# Verificar migraciones aplicadas
alembic current

# Verificar en Dashboard
# Database > Tables > Verificar que HLP_CATEGORIAS y HLP_PETICIONES existan
```

### Comandos SQL Útiles

```sql
-- Ver todas las tablas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Ver estructura de una tabla
\d HLP_PETICIONES

-- Contar registros en HLP_CATEGORIAS
SELECT COUNT(*) FROM HLP_CATEGORIAS;

-- Ver datos seed
SELECT * FROM HLP_CATEGORIAS;

-- Verificar índices
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'HLP_PETICIONES';
```

---

## Redis (Opcional)

Redis es completamente opcional y se usa solo para cache. Si Redis no está disponible, la aplicación funcionará sin cache (degraded pero funcional).

### Configuración Local (Docker)

Si quieres usar Redis localmente durante desarrollo:

1. Inicia Redis con Docker:
```bash
docker-compose up -d redis
```

2. Configura en `.env`:
```env
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Configuración Externa

Si quieres usar Redis desde un servicio externo (ej: Upstash, Redis Cloud):

1. Obtén las credenciales de tu servicio Redis
2. Configura en `.env`:
```env
REDIS_ENABLED=true
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_DB=0
# Si requiere autenticación, agrega:
# REDIS_PASSWORD=your-password
```

### Verificar Redis

```bash
# Verificar que Redis está corriendo (si es local)
docker ps | grep redis

# Verificar conexión desde Python
python -c "from redis import Redis; r = Redis(host='localhost', port=6379); print(r.ping())"
```

---

## Troubleshooting

### Supabase

#### Error: "Connection timeout"

**Solución**: 
- Verifica que la connection string sea correcta
- Verifica que el proyecto de Supabase esté activo
- Verifica tu conexión a internet
- Intenta usar la connection string sin pooling: **Direct connection** en lugar de **Connection Pooling**

#### Error: "password authentication failed"

**Solución**: 
- Verifica que la contraseña en `DATABASE_URL` sea correcta
- La contraseña puede contener caracteres especiales que necesitan ser URL-encoded
- Obtén una nueva connection string desde el Dashboard

#### Error: "permission denied for table"

**Solución**: 
- Verifica que RLS esté configurado correctamente
- Si usas `SUPABASE_SERVICE_ROLE_KEY`, debería bypass RLS automáticamente
- Verifica las políticas RLS en el Dashboard

#### Error: "DATABASE_URL apunta a localhost"

**Solución**: 
- Este proyecto solo soporta Supabase, no PostgreSQL local
- Verifica que `DATABASE_URL` en `.env` apunte a Supabase
- Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String

#### Realtime no funciona

**Solución**:
- Verifica que Realtime esté habilitado para `HLP_PETICIONES` en Database > Replication
- Verifica que los eventos INSERT y UPDATE estén habilitados

#### Migraciones fallan

**Solución**:
- Verifica que `DATABASE_URL` esté correctamente configurada en `.env`
- Verifica que tengas permisos para crear tablas en Supabase
- Revisa los logs de Alembic para más detalles
- Verifica que no haya conflictos con tablas existentes

### General

#### Error: "Module 'alembic' not found"

**Solución**: Instala las dependencias del proyecto.

```bash
# Con uv
uv sync

# Con pip
pip install -r requirements.txt
# o
pip install alembic
```

#### Error: "DATABASE_URL not set"

**Solución**: 
- Verifica que el archivo `.env` exista en `agm-simulated-enviroment/backend/`
- Verifica que `DATABASE_URL` esté definida en `.env`
- Verifica que no haya espacios alrededor del `=` en `.env`

#### Error: "SUPABASE_URL, SUPABASE_ANON_KEY, o SUPABASE_JWT_SECRET no configuradas"

**Solución**:
- Estas variables son requeridas para este proyecto
- Obtén las variables desde: Supabase Dashboard > Settings > API
- Agrega las variables a tu archivo `.env`

#### Redis no está disponible

**Solución**:
- Redis es opcional. Si no está disponible, la aplicación funcionará sin cache
- Si quieres usar Redis, verifica que esté corriendo y configurado correctamente en `.env`
- Verifica que `REDIS_ENABLED=true` si quieres usar Redis

---

## Notas Importantes

- ⚠️ **Nunca commitees el archivo `.env`** con credenciales reales
- ✅ El archivo `.env.example` debe estar commiteado como template
- 🔒 **Mantén `SUPABASE_SERVICE_ROLE_KEY` segura**, permite bypass de RLS
- 📝 **Documenta cambios** en las políticas RLS y configuración de Realtime
- 🔄 **Realtime solo funciona en Supabase**
- 🗺️ **Mapeo de usuarios**: `USUSOLICITA` contiene el username extraído del email del usuario (parte antes de `@`). Ejemplo: `mzuloaga@aguasdemanizales.com.co` → `USUSOLICITA = "mzuloaga"`. El backend extrae automáticamente este valor del JWT del usuario autenticado.
- ⚠️ **Este proyecto solo soporta Supabase**. No se soporta PostgreSQL local.

---

## Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Documentación de Alembic](https://alembic.sqlalchemy.org/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
