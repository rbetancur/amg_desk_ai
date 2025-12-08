#!/bin/bash

# Script para configurar base de datos (PostgreSQL Local o Supabase)
# Uso: ./scripts/setup-db.sh [local|supabase]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Configuración de Base de Datos AGM Desk AI ==="
echo ""

# Si no se proporciona argumento, preguntar
if [ -z "$1" ]; then
    echo "Selecciona el entorno:"
    echo "1) PostgreSQL Local (Docker)"
    echo "2) Supabase (PoC/Producción)"
    read -p "Opción [1/2]: " option
    
    case $option in
        1) ENV="local" ;;
        2) ENV="supabase" ;;
        *)
            echo "❌ Opción inválida"
            exit 1
            ;;
    esac
else
    ENV="$1"
fi

case $ENV in
    local)
        echo "📦 Configurando PostgreSQL Local..."
        
        # Verificar si Docker está corriendo
        if ! docker info > /dev/null 2>&1; then
            echo "❌ Docker no está corriendo. Por favor inicia Docker Desktop."
            exit 1
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
        done
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ PostgreSQL no respondió a tiempo"
            exit 1
        fi
        
        # Verificar si .env existe, si no, crear desde .env.example
        if [ ! -f .env ]; then
            echo "📝 Creando archivo .env desde .env.example..."
            if [ -f .env.example ]; then
                cp .env.example .env
                # Actualizar DATABASE_URL para local
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' 's|# DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db|DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db|' .env
                else
                    sed -i 's|# DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db|DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db|' .env
                fi
                echo "✅ Archivo .env creado. Por favor revisa y ajusta si es necesario."
            else
                echo "⚠️  .env.example no encontrado. Creando .env básico..."
                echo "DATABASE_URL=postgresql://agm_user:agm_password@localhost:5432/agm_desk_db" > .env
            fi
        fi
        
        # Ejecutar migraciones
        echo "🔄 Ejecutando migraciones..."
        if command -v alembic &> /dev/null; then
            alembic upgrade head
        elif [ -f .venv/bin/activate ]; then
            source .venv/bin/activate
            alembic upgrade head
        else
            echo "⚠️  Alembic no encontrado. Por favor ejecuta manualmente: alembic upgrade head"
        fi
        
        echo ""
        echo "✅ Base de datos local configurada exitosamente"
        echo ""
        echo "📋 Información de conexión:"
        echo "   Host: localhost"
        echo "   Puerto: 5432"
        echo "   Usuario: agm_user"
        echo "   Contraseña: agm_password"
        echo "   Base de datos: agm_desk_db"
        echo ""
        echo "💡 Comandos útiles:"
        echo "   Ver logs: docker-compose logs -f postgres"
        echo "   Detener: docker-compose down"
        echo "   Conectar: docker exec -it agm-desk-postgres-local psql -U agm_user -d agm_desk_db"
        ;;
        
    supabase)
        echo "☁️  Configurando Supabase..."
        
        # Verificar si .env existe
        if [ ! -f .env ]; then
            echo "❌ Archivo .env no encontrado."
            echo "📝 Por favor crea el archivo .env con las siguientes variables:"
            echo "   DATABASE_URL=postgresql://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:5432/postgres"
            echo "   SUPABASE_URL=https://[project-ref].supabase.co"
            echo "   SUPABASE_ANON_KEY=..."
            echo "   SUPABASE_SERVICE_ROLE_KEY=..."
            echo ""
            echo "💡 Puedes copiar .env.example como base: cp .env.example .env"
            exit 1
        fi
        
        # Verificar que DATABASE_URL esté configurada
        if ! grep -q "DATABASE_URL=" .env || grep -q "^#.*DATABASE_URL" .env; then
            echo "❌ DATABASE_URL no está configurada en .env"
            echo "   Por favor configura DATABASE_URL con la connection string de Supabase"
            exit 1
        fi
        
        # Ejecutar migraciones
        echo "🔄 Ejecutando migraciones en Supabase..."
        if command -v alembic &> /dev/null; then
            alembic upgrade head
        elif [ -f .venv/bin/activate ]; then
            source .venv/bin/activate
            alembic upgrade head
        else
            echo "⚠️  Alembic no encontrado. Por favor ejecuta manualmente: alembic upgrade head"
        fi
        
        echo ""
        echo "✅ Migraciones aplicadas en Supabase"
        echo ""
        echo "📋 Próximos pasos en Supabase Dashboard:"
        echo "   1. Habilitar Realtime para HLP_PETICIONES:"
        echo "      Database > Replication > HLP_PETICIONES > Enable Realtime"
        echo ""
        echo "   2. Configurar Row Level Security (RLS):"
        echo "      Authentication > Policies > HLP_PETICIONES"
        echo "      Ver documentación en docs/DATABASE_SETUP.md"
        echo ""
        echo "   3. Configurar Autenticación:"
        echo "      Authentication > Providers > Enable Email/Password"
        ;;
        
    *)
        echo "❌ Entorno inválido: $ENV"
        echo "   Uso: $0 [local|supabase]"
        exit 1
        ;;
esac

