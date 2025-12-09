#!/bin/bash

# Script de verificación rápida de conexión y configuración
# Verifica que todo esté configurado correctamente para pruebas desde el frontend
# Uso: ./scripts/verify-connection.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Verificación de Conexión - AGM Desk AI ==="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de errores
ERRORS=0
WARNINGS=0

# Función para imprimir éxito
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para imprimir error
print_error() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS=$((ERRORS + 1))
}

# Función para imprimir advertencia
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

# 1. Verificar archivo .env
echo "📋 Verificando archivo .env..."
if [ ! -f .env ]; then
    print_error "Archivo .env no encontrado"
    echo "   Crea un archivo .env en $BACKEND_DIR con la configuración de Supabase"
    exit 1
else
    print_success "Archivo .env encontrado"
fi

# Cargar variables de entorno de forma segura
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# 2. Verificar variables de entorno requeridas
echo ""
echo "🔍 Verificando variables de entorno..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_JWT_SECRET"
    "API_SECRET_KEY"
    "CORS_ORIGINS"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "$var no está configurada (requerida)"
    else
        if [ "$var" == "DATABASE_URL" ]; then
            # Ocultar contraseña en el output
            DB_URL_DISPLAY=$(echo "$DATABASE_URL" | sed 's/:[^@]*@/:***@/')
            print_success "$var configurada: ${DB_URL_DISPLAY:0:80}..."
        elif [ "$var" == "CORS_ORIGINS" ]; then
            print_success "$var configurada: $CORS_ORIGINS"
        else
            print_success "$var configurada"
        fi
    fi
done

# 3. Validar DATABASE_URL
echo ""
echo "🔍 Validando DATABASE_URL..."
if echo "$DATABASE_URL" | grep -q "localhost\|127.0.0.1"; then
    print_error "DATABASE_URL apunta a localhost"
    echo "   Este proyecto solo soporta Supabase."
    echo "   Obtén la connection string desde: Supabase Dashboard > Settings > Database > Connection String"
elif ! echo "$DATABASE_URL" | grep -qi "supabase"; then
    print_error "DATABASE_URL no apunta a Supabase"
    echo "   Este proyecto solo soporta Supabase como base de datos."
else
    print_success "DATABASE_URL apunta a Supabase"
fi

# 4. Verificar CORS incluye puertos del frontend
echo ""
echo "🔍 Verificando configuración de CORS..."
CORS_INCLUDES_5173=false
CORS_INCLUDES_3000=false

if echo "$CORS_ORIGINS" | grep -q "5173"; then
    CORS_INCLUDES_5173=true
    print_success "CORS incluye http://localhost:5173 (puerto por defecto de Vite)"
else
    print_warning "CORS no incluye http://localhost:5173 (puerto por defecto de Vite)"
    echo "   Considera agregar 'http://localhost:5173' a CORS_ORIGINS en .env"
fi

if echo "$CORS_ORIGINS" | grep -q "3000"; then
    CORS_INCLUDES_3000=true
    print_success "CORS incluye http://localhost:3000"
else
    print_warning "CORS no incluye http://localhost:3000"
    echo "   Considera agregar 'http://localhost:3000' a CORS_ORIGINS en .env"
fi

# 5. Verificar conexión a la base de datos
echo ""
echo "🔄 Verificando conexión a Supabase..."

if command -v python3 &> /dev/null; then
    # Activar entorno virtual si existe
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    python3 -c "
import asyncio
import sys
try:
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
" 2>/dev/null || {
    print_error "No se pudo conectar a Supabase"
    echo "   Verifica que DATABASE_URL sea correcta y que el proyecto de Supabase esté activo"
    ERRORS=$((ERRORS + 1))
}
else
    print_warning "Python no está disponible para verificar conexión"
    echo "   Verifica manualmente ejecutando: alembic current"
fi

# 6. Verificar que el backend esté corriendo (opcional)
echo ""
echo "🔍 Verificando si el backend está corriendo..."
if command -v curl &> /dev/null; then
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
        if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
            print_success "Backend está corriendo y saludable"
            echo "   Health check: $HEALTH_RESPONSE"
        else
            print_warning "Backend está corriendo pero con problemas"
            echo "   Health check: $HEALTH_RESPONSE"
        fi
    else
        print_warning "Backend no está corriendo en http://localhost:8000"
        echo "   Inicia el backend con: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    fi
else
    print_warning "curl no está disponible para verificar el backend"
fi

# 7. Verificar configuración del frontend
echo ""
echo "🔍 Verificando configuración del frontend..."
FRONTEND_DIR="$(cd "$BACKEND_DIR/../frontend" && pwd)"

if [ -f "$FRONTEND_DIR/.env.local" ]; then
    print_success "Archivo .env.local encontrado en frontend"
    if grep -q "VITE_BACKEND_URL" "$FRONTEND_DIR/.env.local"; then
        BACKEND_URL=$(grep "VITE_BACKEND_URL" "$FRONTEND_DIR/.env.local" | cut -d '=' -f2 | tr -d ' ')
        if [ "$BACKEND_URL" == "http://localhost:8000" ]; then
            print_success "VITE_BACKEND_URL configurado correctamente: $BACKEND_URL"
        else
            print_warning "VITE_BACKEND_URL está configurado como: $BACKEND_URL"
            echo "   Asegúrate de que apunte a http://localhost:8000 para desarrollo local"
        fi
    else
        print_warning "VITE_BACKEND_URL no encontrado en .env.local"
        echo "   El frontend usará el valor por defecto: http://localhost:8000"
    fi
else
    print_warning "Archivo .env.local no encontrado en frontend"
    echo "   El frontend usará valores por defecto desde constants.ts"
    echo "   Considera crear .env.local con VITE_BACKEND_URL=http://localhost:8000"
fi

# Resumen
echo ""
echo "=== Resumen ==="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_success "¡Todo está configurado correctamente!"
    echo ""
    echo "📝 Próximos pasos:"
    echo "   1. Inicia el backend: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo "   2. En otra terminal, inicia el frontend: cd ../frontend && npm run dev"
    echo "   3. Abre http://localhost:5173 (o el puerto que use Vite) en tu navegador"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    print_warning "Configuración completa con $WARNINGS advertencia(s)"
    echo ""
    echo "📝 Puedes continuar, pero considera revisar las advertencias arriba"
    exit 0
else
    print_error "Se encontraron $ERRORS error(es) y $WARNINGS advertencia(s)"
    echo ""
    echo "📝 Corrige los errores antes de continuar"
    exit 1
fi

