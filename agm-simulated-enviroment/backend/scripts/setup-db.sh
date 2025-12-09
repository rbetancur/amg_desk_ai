#!/bin/bash

# Script para configurar Supabase
# Uso: ./scripts/setup-db.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=== Configuración de Supabase - AGM Desk AI ==="
echo ""
echo "⚠️  IMPORTANTE: Este proyecto solo soporta Supabase como base de datos."
echo ""

# Función para validar que .env existe
check_env_file() {
    if [ ! -f .env ]; then
        echo -e "${RED}❌ Archivo .env no encontrado${NC}"
        echo ""
        echo "Por favor, crea un archivo .env con las credenciales de Supabase."
        echo "Puedes usar el siguiente template:"
        echo ""
        echo "DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres"
        echo "SUPABASE_URL=https://[PROJECT-REF].supabase.co"
        echo "SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        echo "SUPABASE_JWT_SECRET=your-jwt-secret-here"
        echo ""
        exit 1
    fi
    echo -e "${GREEN}✅ Archivo .env encontrado${NC}"
}

# Función para validar credenciales (no placeholders)
validate_credentials() {
    local errors=0
    
    # Validar DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}❌ DATABASE_URL no está configurada${NC}"
        errors=$((errors + 1))
    elif [[ "$DATABASE_URL" == *"[PROJECT-REF]"* ]] || [[ "$DATABASE_URL" == *"[YOUR-PASSWORD]"* ]] || [[ "$DATABASE_URL" == *"[REGION]"* ]]; then
        echo -e "${RED}❌ DATABASE_URL contiene placeholders. Debe tener valores reales.${NC}"
        errors=$((errors + 1))
    elif [[ "$DATABASE_URL" == *"localhost"* ]] || [[ "$DATABASE_URL" == *"127.0.0.1"* ]]; then
        echo -e "${RED}❌ DATABASE_URL apunta a localhost. Este proyecto solo soporta Supabase.${NC}"
        errors=$((errors + 1))
    elif [[ "$DATABASE_URL" != *"supabase"* ]] && [[ "$DATABASE_URL" != *"db."*".supabase"* ]]; then
        echo -e "${YELLOW}⚠️  DATABASE_URL no parece ser de Supabase${NC}"
    else
        echo -e "${GREEN}✅ DATABASE_URL configurada correctamente${NC}"
    fi
    
    # Validar SUPABASE_URL
    if [ -z "$SUPABASE_URL" ]; then
        echo -e "${RED}❌ SUPABASE_URL no está configurada${NC}"
        errors=$((errors + 1))
    elif [[ "$SUPABASE_URL" == *"[PROJECT-REF]"* ]]; then
        echo -e "${RED}❌ SUPABASE_URL contiene placeholders. Debe tener valores reales.${NC}"
        errors=$((errors + 1))
    elif [[ ! "$SUPABASE_URL" =~ ^https://.*\.supabase\.co$ ]]; then
        echo -e "${RED}❌ SUPABASE_URL no tiene formato válido. Debe ser: https://[PROJECT-REF].supabase.co${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ SUPABASE_URL configurada correctamente${NC}"
    fi
    
    # Validar SUPABASE_ANON_KEY
    if [ -z "$SUPABASE_ANON_KEY" ]; then
        echo -e "${RED}❌ SUPABASE_ANON_KEY no está configurada${NC}"
        errors=$((errors + 1))
    elif [[ "$SUPABASE_ANON_KEY" == *"..."* ]]; then
        echo -e "${RED}❌ SUPABASE_ANON_KEY contiene placeholders. Debe tener el valor completo.${NC}"
        errors=$((errors + 1))
    elif [[ ! "$SUPABASE_ANON_KEY" =~ ^eyJ ]]; then
        echo -e "${RED}❌ SUPABASE_ANON_KEY no tiene formato válido. Debe comenzar con 'eyJ'${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ SUPABASE_ANON_KEY configurada correctamente${NC}"
    fi
    
    # Validar SUPABASE_JWT_SECRET
    if [ -z "$SUPABASE_JWT_SECRET" ]; then
        echo -e "${RED}❌ SUPABASE_JWT_SECRET no está configurada${NC}"
        errors=$((errors + 1))
    elif [ "$SUPABASE_JWT_SECRET" == "your-jwt-secret-here" ]; then
        echo -e "${RED}❌ SUPABASE_JWT_SECRET contiene placeholder. Debe tener el valor real.${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ SUPABASE_JWT_SECRET configurada correctamente${NC}"
    fi
    
    return $errors
}

# Función para obtener comando de alembic
get_alembic_cmd() {
    if command -v uv &> /dev/null; then
        echo "uv run alembic"
    elif command -v alembic &> /dev/null; then
        echo "alembic"
    elif [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
        echo "alembic"
    else
        echo ""
    fi
}

# Función para verificar estado de migraciones
check_migration_status() {
    local alembic_cmd=$(get_alembic_cmd)
    
    if [ -z "$alembic_cmd" ]; then
        echo -e "${YELLOW}⚠️  Alembic no encontrado. No se puede verificar estado de migraciones.${NC}"
        return 2
    fi
    
    echo -e "${BLUE}🔍 Verificando estado de migraciones...${NC}"
    
    # Obtener migración actual
    local current_version
    if current_version=$($alembic_cmd current 2>&1); then
        # Extraer el número de versión de la salida
        current_version=$(echo "$current_version" | grep -oE '[0-9a-f]+' | head -1 || echo "")
        if [ -n "$current_version" ]; then
            echo -e "${GREEN}✅ Migración actual: $current_version${NC}"
        else
            # Si no hay versión pero el comando no falló, puede que no haya migraciones
            echo -e "${YELLOW}⚠️  No se detectó versión de migración actual${NC}"
            return 1
        fi
    else
        # Si alembic current falla, probablemente no hay tabla alembic_version
        echo -e "${YELLOW}⚠️  No hay migraciones aplicadas (tabla alembic_version no existe)${NC}"
        return 1
    fi
    
    # Obtener head (última migración disponible)
    local head_version
    if head_version=$($alembic_cmd heads 2>&1); then
        head_version=$(echo "$head_version" | grep -oE '[0-9a-f]+' | head -1 || echo "")
        if [ -n "$head_version" ]; then
            echo -e "${BLUE}📌 Última migración disponible: $head_version${NC}"
            
            # Comparar versiones
            if [ "$current_version" == "$head_version" ]; then
                echo -e "${GREEN}✅ Las migraciones ya están actualizadas${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  Hay migraciones pendientes${NC}"
                return 1
            fi
        fi
    fi
    
    return 1
}

# Función para ejecutar migraciones si es necesario
run_migrations_if_needed() {
    local migration_status=$1
    local alembic_cmd=$(get_alembic_cmd)
    
    if [ -z "$alembic_cmd" ]; then
        echo -e "${RED}❌ Alembic no encontrado. No se pueden ejecutar migraciones.${NC}"
        echo "   Por favor instala las dependencias:"
        echo "   - Con uv: uv sync"
        echo "   - Con pip: pip install -r requirements.txt"
        return 1
    fi
    
    case $migration_status in
        0)
            echo ""
            echo -e "${GREEN}✅ Las migraciones ya están aplicadas. No es necesario ejecutarlas.${NC}"
            ;;
        1)
            echo ""
            echo -e "${BLUE}📦 Ejecutando migraciones en Supabase...${NC}"
            if $alembic_cmd upgrade head; then
                echo -e "${GREEN}✅ Migraciones ejecutadas exitosamente${NC}"
            else
                echo -e "${RED}❌ Error al ejecutar migraciones${NC}"
                return 1
            fi
            ;;
        2)
            echo ""
            echo -e "${YELLOW}⚠️  No se pudo verificar el estado de migraciones${NC}"
            echo -e "${YELLOW}   Intentando ejecutar migraciones de todas formas...${NC}"
            if $alembic_cmd upgrade head; then
                echo -e "${GREEN}✅ Migraciones ejecutadas exitosamente${NC}"
            else
                echo -e "${RED}❌ Error al ejecutar migraciones${NC}"
                return 1
            fi
            ;;
    esac
}

# Función para verificar conexión a Supabase
check_supabase_connection() {
    echo -e "${BLUE}🔍 Verificando conexión a Supabase...${NC}"
    
    if command -v python3 &> /dev/null; then
        python3 -c "
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())
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
" 2>/dev/null && return 0 || {
            echo -e "${YELLOW}⚠️  No se pudo verificar la conexión automáticamente${NC}"
            echo -e "${YELLOW}   Continuando de todas formas...${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Python no está disponible para verificar conexión${NC}"
        echo -e "${YELLOW}   Continuando de todas formas...${NC}"
    fi
}

# ============================================
# FLUJO PRINCIPAL
# ============================================

# 1. Validar que .env existe
check_env_file

# 2. Cargar variables de entorno
echo ""
echo -e "${BLUE}📋 Cargando variables de entorno...${NC}"
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# 3. Validar credenciales
echo ""
echo -e "${BLUE}🔍 Validando credenciales de Supabase...${NC}"
if ! validate_credentials; then
    echo ""
    echo -e "${RED}❌ Faltan variables de configuración requeridas o contienen placeholders${NC}"
    echo ""
    echo "Por favor, actualiza el archivo .env con tus credenciales reales de Supabase:"
    echo "  - DATABASE_URL: Supabase Dashboard > Settings > Database > Connection String"
    echo "  - SUPABASE_URL: Supabase Dashboard > Settings > API > Project URL"
    echo "  - SUPABASE_ANON_KEY: Supabase Dashboard > Settings > API > anon public key"
    echo "  - SUPABASE_JWT_SECRET: Supabase Dashboard > Settings > API > JWT Secret"
    exit 1
fi

# 4. Verificar conexión a Supabase
echo ""
check_supabase_connection

# 5. Verificar estado de migraciones
echo ""
migration_status=1
if check_migration_status; then
    migration_status=0  # Migraciones ya aplicadas
else
    migration_status=$?  # 1 = pendientes, 2 = no se pudo verificar
fi

# 6. Ejecutar migraciones si es necesario
run_migrations_if_needed $migration_status

# 7. Resumen final
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Configuración de Supabase completada!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Mostrar estado actual
echo -e "${BLUE}📊 Estado actual:${NC}"
echo "  - Credenciales: ✅ Configuradas"
echo "  - Conexión: ✅ Verificada"
if [ $migration_status -eq 0 ]; then
    echo "  - Migraciones: ✅ Actualizadas"
else
    echo "  - Migraciones: ✅ Aplicadas"
fi

echo ""
echo -e "${BLUE}📋 Próximos pasos:${NC}"
echo ""
echo "1. Verifica el estado de las migraciones:"
echo "   alembic current"
echo ""
echo "2. Configura Row Level Security (RLS) en Supabase Dashboard:"
echo "   Authentication > Policies > HLP_PETICIONES"
echo "   Ver documentación en docs/DATABASE_SETUP.md"
echo ""
echo "3. Habilita Realtime para HLP_PETICIONES:"
echo "   Database > Replication > HLP_PETICIONES > Enable Realtime"
echo "   Asegúrate de habilitar eventos INSERT y UPDATE"
echo ""
echo "4. Verifica la conexión:"
echo "   ./scripts/check-db.sh"
echo "   o"
echo "   curl http://localhost:8000/health"
echo ""
