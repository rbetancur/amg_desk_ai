# Instrucciones para Iniciar Base de Datos Local

> **Nota**: Estas instrucciones son para PostgreSQL local con Docker, que es **opcional**. Se recomienda usar **Supabase** como método principal. Ver `agm-simulated-enviroment/backend/docs/DATABASE_SETUP.md` para configuración con Supabase.

## Opción 1: Usar el Script Automático (Solo para PostgreSQL Local)

```bash
cd agm-simulated-enviroment/backend
./scripts/iniciar-bd-local.sh
```

Este script:
- Verifica que Docker esté disponible
- Inicia el contenedor PostgreSQL
- Espera a que esté listo
- Ejecuta las migraciones automáticamente

## Opción 2: Manual

### 1. Verificar Docker

```bash
docker --version
docker info
```

Si Docker no está instalado:
- Descarga Docker Desktop desde https://www.docker.com/products/docker-desktop
- Instálalo e inícialo

### 2. Iniciar PostgreSQL

```bash
cd agm-simulated-enviroment/backend
docker-compose up -d
```

### 3. Verificar que está corriendo

```bash
docker ps | grep postgres
```

### 4. Ejecutar Migraciones

```bash
# Con uv
uv run alembic upgrade head

# O con pip/venv
source .venv/bin/activate
alembic upgrade head
```

### 5. Verificar Tablas

```bash
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "\dt"
```

Deberías ver:
- `HLP_CATEGORIAS`
- `HLP_PETICIONES`

### 6. Ver Categorías Iniciales

```bash
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c "SELECT * FROM HLP_CATEGORIAS;"
```

## Comandos Útiles

### Ver logs de PostgreSQL

```bash
docker-compose logs -f postgres
```

### Conectar a PostgreSQL

```bash
docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db
```

### Detener PostgreSQL

```bash
docker-compose down
```

### Detener y eliminar datos

```bash
docker-compose down -v
```

## Solución de Problemas

### Error: "Docker no está corriendo"

1. Abre Docker Desktop
2. Espera a que inicie completamente
3. Verifica con: `docker info`

### Error: "Puerto 5432 ya en uso"

Si ya tienes PostgreSQL corriendo en el puerto 5432:

1. Detén el otro servicio de PostgreSQL
2. O cambia el puerto en `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Cambiar a otro puerto
   ```
3. Actualiza `DATABASE_URL` en `.env`:
   ```
   DATABASE_URL=postgresql://agm_user:agm_password@localhost:5433/agm_desk_db
   ```

### Error: "No se pueden ejecutar migraciones"

1. Verifica que el archivo `.env` existe y tiene `DATABASE_URL` correcta
2. Verifica que PostgreSQL está corriendo: `docker ps | grep postgres`
3. Prueba la conexión manualmente:
   ```bash
   docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db
   ```

## Método Recomendado: Usar Supabase

> **Nota**: Supabase es el método **recomendado** para desarrollo y producción. No requiere Docker y es más simple de configurar.

1. Crea una cuenta en https://supabase.com
2. Crea un nuevo proyecto
3. Obtén las credenciales desde Project Settings > Database (connection string) y Settings > API (API keys)
4. Actualiza el archivo `.env`:
   ```env
   DATABASE_URL=postgresql://postgres.[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[PROJECT-REF].supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_JWT_SECRET=your-jwt-secret-here
   ```
5. Ejecuta migraciones: `alembic upgrade head`

Ver más detalles en: `agm-simulated-enviroment/backend/docs/DATABASE_SETUP.md`
