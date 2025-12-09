#!/bin/bash

# Script para iniciar PostgreSQL local con Docker
# Uso: ./scripts/iniciar-bd-local.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Iniciando Base de Datos Local ==="
echo ""

# Verificar si Docker está disponible
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está disponible en el PATH"
    echo ""
    echo "Por favor:"
    echo "1. Instala Docker Desktop desde https://www.docker.com/products/docker-desktop"
    echo "2. Inicia Docker Desktop"
    echo "3. Ejecuta este script nuevamente"
    exit 1
fi

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo"
    echo ""
    echo "Por favor inicia Docker Desktop y ejecuta este script nuevamente"
    exit 1
fi

echo "✅ Docker está disponible y corriendo"
echo ""

# Verificar si el contenedor ya está corriendo
if docker ps | grep -q "agm-desk-postgres-local"; then
    echo "✅ PostgreSQL ya está corriendo"
    echo ""
    docker ps | grep "agm-desk-postgres-local"
    exit 0
fi

# Iniciar PostgreSQL
echo "🚀 Iniciando contenedor PostgreSQL..."
docker-compose up -d

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U agm_user -d agm_desk_db > /dev/null 2>&1; then
        echo "✅ PostgreSQL está listo"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
    echo -n "."
done
echo ""

if [ $attempt -eq $max_attempts ]; then
    echo "❌ PostgreSQL no respondió a tiempo"
    exit 1
fi

# Verificar archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "Creando archivo .env desde configuración..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db
API_SECRET_KEY=dev-api-secret-key-12345
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
PROJECT_NAME=AGM Desk AI Backend
VERSION=0.1.0
EOF
    echo "✅ Archivo .env creado"
fi

# Ejecutar migraciones
echo ""
echo "📦 Ejecutando migraciones..."
if command -v uv &> /dev/null; then
    uv run alembic upgrade head
else
    source .venv/bin/activate
    alembic upgrade head
fi

echo ""
echo "✅ Base de datos lista!"
echo ""
echo "Información de conexión:"
echo "  - Host: localhost"
echo "  - Puerto: 5432"
echo "  - Usuario: agm_user"
echo "  - Contraseña: agm_password"
echo "  - Base de datos: agm_desk_db"
echo ""
echo "Para verificar las tablas:"
echo "  docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db -c '\\dt'"
echo ""
echo "Para detener PostgreSQL:"
echo "  docker-compose down"
echo ""

