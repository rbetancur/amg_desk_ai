#!/bin/bash
# Script simple para verificar tablas usando psql si está disponible
# Uso: ./scripts/verify-tables-simple.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

echo "=== Verificación de Tablas en Supabase ==="
echo ""
echo "📋 Para verificar las tablas, puedes:"
echo ""
echo "1. Usar el Dashboard de Supabase:"
echo "   https://supabase.com/dashboard/project/jqzuacudoegneaueroan"
echo "   Database > Tables"
echo ""
echo "2. Usar el SQL Editor en Supabase:"
echo "   Dashboard > SQL Editor"
echo "   Ejecuta: SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
echo ""
echo "3. Si tienes psql instalado, puedes conectar directamente:"
echo "   psql \"$DATABASE_URL\" -c \"\\dt\""
echo ""
echo "4. Si tienes las dependencias Python instaladas:"
echo "   source .venv/bin/activate"
echo "   python scripts/verify-tables.py"
echo ""
