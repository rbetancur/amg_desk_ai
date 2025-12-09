#!/bin/bash

# Script para verificar conexión y estado de Supabase
# Uso: ./scripts/check-db.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Verificación de Supabase - AGM Desk AI ==="
echo ""

# Verificar si .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    echo "   Crea un archivo .env en $BACKEND_DIR con la configuración de Supabase"
    exit 1
fi

# Cargar variables de entorno
export $(grep -v '^#' .env | xargs)

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL no está configurada en .env"
    echo "   Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
    exit 1
fi

# Validar que DATABASE_URL no apunte a localhost
if echo "$DATABASE_URL" | grep -q "localhost\|127.0.0.1"; then
    echo "❌ ERROR: DATABASE_URL apunta a localhost"
    echo "   Este proyecto solo soporta Supabase."
    echo "   Por favor, configura DATABASE_URL con la connection string de Supabase."
    echo "   Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
    exit 1
fi

# Validar que DATABASE_URL apunte a Supabase
if ! echo "$DATABASE_URL" | grep -qi "supabase"; then
    echo "❌ ERROR: DATABASE_URL no apunta a Supabase"
    echo "   Este proyecto solo soporta Supabase como base de datos."
    echo "   Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
    exit 1
fi

echo "📋 Configuración detectada:"
echo "   DATABASE_URL: ${DATABASE_URL:0:60}..."
echo ""

# Verificar variables de Supabase requeridas
echo "🔍 Verificando variables de Supabase..."
echo ""

MISSING_VARS=0

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL no configurada (requerida)"
    MISSING_VARS=$((MISSING_VARS + 1))
else
    echo "✅ SUPABASE_URL configurada: ${SUPABASE_URL}"
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ SUPABASE_ANON_KEY no configurada (requerida)"
    MISSING_VARS=$((MISSING_VARS + 1))
else
    echo "✅ SUPABASE_ANON_KEY configurada"
fi

if [ -z "$SUPABASE_JWT_SECRET" ]; then
    echo "❌ SUPABASE_JWT_SECRET no configurada (requerida)"
    MISSING_VARS=$((MISSING_VARS + 1))
else
    echo "✅ SUPABASE_JWT_SECRET configurada"
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "⚠️  SUPABASE_SERVICE_ROLE_KEY no configurada (opcional, requerida para Agente AI)"
else
    echo "✅ SUPABASE_SERVICE_ROLE_KEY configurada"
fi

if [ $MISSING_VARS -gt 0 ]; then
    echo ""
    echo "❌ Faltan variables de Supabase requeridas"
    echo "   Obtén las variables desde: Supabase Dashboard > Settings > API"
    exit 1
fi

echo ""
echo "🔄 Verificando conexión a Supabase..."

# Intentar verificar conexión usando Python si está disponible
if command -v python3 &> /dev/null; then
    python3 -c "
import asyncio
import sys
from app.db.base import engine
from sqlalchemy import text

async def check_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        print('✅ Conexión a Supabase exitosa')
        return True
    except Exception as e:
        print(f'❌ Error al conectar a Supabase: {e}')
        return False

if not asyncio.run(check_connection()):
    sys.exit(1)
" || {
    echo ""
    echo "⚠️  No se pudo verificar la conexión automáticamente"
    echo "   Verifica manualmente que DATABASE_URL sea correcta"
    echo "   O ejecuta: alembic current"
}
else
    echo "⚠️  Python no está disponible para verificar conexión"
    echo "   Verifica manualmente ejecutando: alembic current"
fi

echo ""
echo "✅ Verificación completada"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Si las migraciones no se han ejecutado: alembic upgrade head"
echo "   2. Verifica el estado de las migraciones: alembic current"
echo "   3. Verifica el endpoint de health: curl http://localhost:8000/health"
