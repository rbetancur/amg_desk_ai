#!/bin/bash

# Script para verificar conexión y estado de la base de datos
# Uso: ./scripts/check-db.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Verificación de Base de Datos AGM Desk AI ==="
echo ""

# Verificar si .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Cargar variables de entorno
export $(grep -v '^#' .env | xargs)

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL no está configurada en .env"
    exit 1
fi

echo "📋 Configuración detectada:"
echo "   DATABASE_URL: ${DATABASE_URL:0:50}..."
echo ""

# Detectar tipo de base de datos
if echo "$DATABASE_URL" | grep -q "localhost\|127.0.0.1"; then
    DB_TYPE="local"
    echo "🔍 Tipo: PostgreSQL Local"
    
    # Verificar si Docker está corriendo
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker no está corriendo"
        exit 1
    fi
    
    # Verificar si el contenedor está corriendo
    if ! docker ps | grep -q "agm-desk-postgres-local"; then
        echo "⚠️  Contenedor PostgreSQL no está corriendo"
        echo "   Ejecuta: docker-compose up -d"
        exit 1
    fi
    
    echo "✅ Contenedor PostgreSQL está corriendo"
    
    # Verificar conexión
    echo "🔄 Verificando conexión..."
    if docker-compose exec -T postgres pg_isready -U agm_user -d agm_desk_db > /dev/null 2>&1; then
        echo "✅ Conexión exitosa"
    else
        echo "❌ No se pudo conectar a PostgreSQL"
        exit 1
    fi
    
    # Verificar tablas
    echo "🔄 Verificando tablas..."
    TABLES=$(docker-compose exec -T postgres psql -U agm_user -d agm_desk_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    if [ "$TABLES" -gt "0" ]; then
        echo "✅ Tablas encontradas: $TABLES"
        echo ""
        echo "📊 Tablas en la base de datos:"
        docker-compose exec -T postgres psql -U agm_user -d agm_desk_db -c "\dt" 2>/dev/null || echo "   (No se pudieron listar las tablas)"
    else
        echo "⚠️  No se encontraron tablas. Ejecuta migraciones: alembic upgrade head"
    fi
    
    # Verificar datos seed
    echo ""
    echo "🔄 Verificando datos seed (HLP_CATEGORIAS)..."
    CATEGORIES=$(docker-compose exec -T postgres psql -U agm_user -d agm_desk_db -t -c "SELECT COUNT(*) FROM HLP_CATEGORIAS;" | tr -d ' ')
    echo "   Categorías encontradas: $CATEGORIES"
    if [ "$CATEGORIES" -gt "0" ]; then
        echo "   Detalles:"
        docker-compose exec -T postgres psql -U agm_user -d agm_desk_db -c "SELECT CODCATEGORIA, CATEGORIA FROM HLP_CATEGORIAS;" 2>/dev/null || true
    fi
    
else
    DB_TYPE="supabase"
    echo "🔍 Tipo: Supabase"
    
    # Verificar variables de Supabase
    if [ -n "$SUPABASE_URL" ]; then
        echo "✅ SUPABASE_URL configurada"
    else
        echo "⚠️  SUPABASE_URL no configurada (opcional)"
    fi
    
    if [ -n "$SUPABASE_ANON_KEY" ]; then
        echo "✅ SUPABASE_ANON_KEY configurada"
    else
        echo "⚠️  SUPABASE_ANON_KEY no configurada (opcional)"
    fi
    
    if [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
        echo "✅ SUPABASE_SERVICE_ROLE_KEY configurada"
    else
        echo "⚠️  SUPABASE_SERVICE_ROLE_KEY no configurada (opcional, requerida para Agente AI)"
    fi
    
    echo ""
    echo "🔄 Para verificar conexión a Supabase, ejecuta:"
    echo "   alembic current"
    echo "   o"
    echo "   python -c 'from app.db.base import engine; import asyncio; asyncio.run(engine.connect())'"
fi

echo ""
echo "✅ Verificación completada"

