# Guía de Configuración de Base de Datos

Esta guía explica cómo configurar la base de datos para el proyecto AGM Desk AI. El proyecto soporta dos entornos:

1. **PostgreSQL Local (Docker)**: Para desarrollo y pruebas locales
2. **Supabase**: Para PoC y producción, con Realtime y RLS configurados

## Tabla de Contenidos

- [PostgreSQL Local](#postgresql-local)
- [Supabase](#supabase)
- [Migraciones](#migraciones)
- [Verificación](#verificación)
- [Troubleshooting](#troubleshooting)

---

## PostgreSQL Local

### Requisitos

- Docker Desktop instalado y corriendo
- Docker Compose (incluido en Docker Desktop)

### Configuración Paso a Paso

#### 1. Iniciar PostgreSQL con Docker

```bash
cd agm-simulated-enviroment/backend
docker-compose up -d
```

Esto iniciará un contenedor PostgreSQL 16 con las siguientes credenciales:
- **Usuario**: `agm_user`
- **Contraseña**: `agm_password`
- **Base de datos**: `agm_desk_db`
- **Puerto**: `5432`

#### 2. Verificar que PostgreSQL esté corriendo

```bash
docker ps | grep postgres
```

Deberías ver el contenedor `agm-desk-postgres-local` en la lista.

#### 3. Configurar archivo .env

Crea un archivo `.env` en `agm-simulated-enviroment/backend/` con el siguiente contenido:

```env
DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0
```

O copia desde `.env.example` y descomenta la línea de PostgreSQL Local.

#### 4. Ejecutar migraciones

```bash
# Activar entorno virtual si es necesario
source .venv/bin/activate

# Ejecutar migraciones
alembic upgrade head
```

#### 5. Verificar tablas creadas

```bash
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "\dt"
```

Deberías ver las tablas `HLP_CATEGORIAS` y `HLP_PETICIONES`.

### Comandos Útiles

```bash
# Ver logs de PostgreSQL
docker-compose logs -f postgres

# Detener PostgreSQL
docker-compose down

# Detener y eliminar volúmenes (⚠️ elimina todos los datos)
docker-compose down -v

# Conectar a PostgreSQL con psql
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db

# Verificar datos seed
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "SELECT * FROM HLP_CATEGORIAS;"
```

### Usando el Script de Configuración

Puedes usar el script automatizado:

```bash
./scripts/setup-db.sh local
```

Este script:
- Verifica que Docker esté corriendo
- Inicia el contenedor PostgreSQL
- Espera a que PostgreSQL esté listo
- Crea el archivo `.env` si no existe
- Ejecuta las migraciones automáticamente

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
   - **service_role key**: ⚠️ **Mantén esta clave segura**, permite bypass de RLS

#### 4. Configurar archivo .env

Crea un archivo `.env` en `agm-simulated-enviroment/backend/` con el siguiente contenido:

```env
# Connection String de Supabase
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres

# API Keys de Supabase
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Configuración de la aplicación
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0
```

Reemplaza los valores entre corchetes con tus credenciales reales.

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

**Nota**: Realtime solo funciona en Supabase, no en PostgreSQL local. Para desarrollo local, el Agente AI puede usar polling como alternativa.

#### 7. Configurar Row Level Security (RLS)

RLS asegura que los usuarios solo puedan ver y editar sus propias solicitudes.

##### Habilitar RLS en la tabla

1. Ve a **Database** > **Tables**
2. Selecciona la tabla `HLP_PETICIONES`
3. Haz clic en el ícono de candado (🔒) junto al nombre de la tabla
4. Activa **Enable Row Level Security**

##### Crear Políticas RLS

Ve a **Authentication** > **Policies** y crea las siguientes políticas:

**Política 1: Usuarios pueden ver sus propias solicitudes**

- **Name**: `Users can view own requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `SELECT`
- **Policy definition**: Usa el editor SQL y pega:

```sql
(
  (SELECT auth.uid()::text) = "USUSOLICITA"
)
```

**Nota**: Esta política asume que `USUSOLICITA` contiene el UUID del usuario de Supabase. Si usas un mapeo diferente (ej: email), ajusta la expresión.

**Política 2: Usuarios pueden crear solicitudes**

- **Name**: `Users can create requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `INSERT`
- **Policy definition**:

```sql
(
  (SELECT auth.uid()::text) = "USUSOLICITA"
)
```

**Política 3: Usuarios pueden actualizar sus propias solicitudes (opcional)**

- **Name**: `Users can update own requests`
- **Table**: `HLP_PETICIONES`
- **Operation**: `UPDATE`
- **Policy definition**:

```sql
(
  (SELECT auth.uid()::text) = "USUSOLICITA"
)
```

**Nota sobre Service Role Key**: El `SUPABASE_SERVICE_ROLE_KEY` permite bypass automático de RLS. El Agente AI usará esta clave para leer y actualizar todas las solicitudes sin restricciones.

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
     - Descripción: "Users will be required to confirm any email change on both the old email address and new email address"
   
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

# Verificar tablas
# En Supabase Dashboard > Database > Tables
```

### Usando el Script de Configuración

Puedes usar el script automatizado:

```bash
./scripts/setup-db.sh supabase
```

Este script:
- Verifica que el archivo `.env` exista
- Verifica que `DATABASE_URL` esté configurada
- Ejecuta las migraciones automáticamente
- Muestra los próximos pasos en el Dashboard

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
- Conexión a la base de datos
- Estado de las tablas
- Datos seed (categorías)

### Verificación Manual

#### PostgreSQL Local

```bash
# Verificar conexión
docker-compose exec postgres pg_isready -U agm_user -d agm_desk_db

# Listar tablas
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "\dt"

# Verificar datos seed
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "SELECT * FROM HLP_CATEGORIAS;"
```

#### Supabase

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

## Troubleshooting

### PostgreSQL Local

#### Error: "Docker no está corriendo"

**Solución**: Inicia Docker Desktop y espera a que esté completamente iniciado.

#### Error: "Port 5432 is already allocated"

**Solución**: Otra instancia de PostgreSQL está usando el puerto 5432.

```bash
# Ver qué proceso está usando el puerto
lsof -i :5432

# O cambiar el puerto en docker-compose.yml
ports:
  - "5433:5432"  # Cambiar 5432 a 5433
```

#### Error: "Connection refused"

**Solución**: El contenedor no está corriendo o no está listo.

```bash
# Verificar estado del contenedor
docker ps -a | grep postgres

# Ver logs
docker-compose logs postgres

# Reiniciar contenedor
docker-compose restart postgres
```

#### Error: "relation does not exist"

**Solución**: Las migraciones no se han ejecutado.

```bash
# Ejecutar migraciones
alembic upgrade head
```

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

#### Realtime no funciona

**Solución**:
- Verifica que Realtime esté habilitado para `HLP_PETICIONES` en Database > Replication
- Verifica que los eventos INSERT y UPDATE estén habilitados
- Realtime solo funciona en Supabase, no en PostgreSQL local

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

---

## Notas Importantes

- ⚠️ **Nunca commitees el archivo `.env`** con credenciales reales
- ✅ El archivo `.env.example` debe estar commiteado como template
- 🔒 **Mantén `SUPABASE_SERVICE_ROLE_KEY` segura**, permite bypass de RLS
- 📝 **Documenta cambios** en las políticas RLS y configuración de Realtime
- 🔄 **Realtime solo funciona en Supabase**, no en PostgreSQL local
- 🗺️ **Mapeo de usuarios**: Asegúrate de que `USUSOLICITA` coincida con el formato esperado (UUID de Supabase o email según tu implementación)

---

## Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Documentación de Alembic](https://alembic.sqlalchemy.org/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación de Docker Compose](https://docs.docker.com/compose/)

