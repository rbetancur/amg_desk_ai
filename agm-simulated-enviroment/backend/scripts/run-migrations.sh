#!/bin/bash
# Script para ejecutar migraciones en Supabase
# Este script instala las dependencias necesarias y ejecuta las migraciones

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Ejecutando Migraciones en Supabase ==="
echo ""

# Verificar que .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    echo "   Por favor crea el archivo .env con DATABASE_URL configurada"
    exit 1
fi

# Verificar que DATABASE_URL esté configurada
if ! grep -q "DATABASE_URL=" .env || grep -q "^#.*DATABASE_URL" .env; then
    echo "❌ DATABASE_URL no está configurada en .env"
    exit 1
fi

echo "📦 Instalando dependencias necesarias..."
echo ""

# Intentar con pip3 del sistema
if command -v pip3 &> /dev/null; then
    echo "   Usando pip3 del sistema..."
    pip3 install --user alembic sqlalchemy psycopg2-binary --quiet
    PYTHON_CMD="python3"
    ALEMBIC_CMD="$HOME/.local/bin/alembic"
    
    # Si alembic no está en .local/bin, intentar con python3 -m
    if [ ! -f "$ALEMBIC_CMD" ]; then
        ALEMBIC_CMD="python3 -m alembic"
    fi
elif command -v python3 &> /dev/null; then
    echo "   Instalando con python3 -m pip..."
    python3 -m pip install --user alembic sqlalchemy psycopg2-binary --quiet
    PYTHON_CMD="python3"
    ALEMBIC_CMD="python3 -m alembic"
else
    echo "❌ No se encontró pip3 ni python3"
    echo ""
    echo "Por favor instala las dependencias manualmente:"
    echo "   pip3 install alembic sqlalchemy psycopg2-binary"
    echo ""
    echo "Luego ejecuta:"
    echo "   alembic upgrade head"
    exit 1
fi

echo "✅ Dependencias instaladas"
echo ""

echo "🔄 Ejecutando migraciones..."
echo ""

# Ejecutar migraciones
if [ -f "$ALEMBIC_CMD" ] || [ "$ALEMBIC_CMD" == "python3 -m alembic" ]; then
    $ALEMBIC_CMD upgrade head
else
    # Intentar con python3 directamente
    cd "$BACKEND_DIR"
    python3 -c "
import sys
sys.path.insert(0, '.')
from alembic.config import Config
from alembic import command

alembic_cfg = Config('alembic.ini')
command.upgrade(alembic_cfg, 'head')
"
fi

echo ""
echo "✅ Migraciones ejecutadas"
echo ""
echo "📋 Verifica en el Dashboard de Supabase:"
echo "   https://supabase.com/dashboard/project/jqzuacudoegneaueroan/database/tables"
echo ""
echo "   Deberías ver las tablas:"
echo "   - HLP_CATEGORIAS"
echo "   - HLP_PETICIONES"
echo "   - alembic_version"

