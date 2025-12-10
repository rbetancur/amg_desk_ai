#!/bin/bash
# Script para actualizar configuración de rate limiting en .env
# Uso: ./scripts/update-rate-limit.sh [enable|disable] [max_requests]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$AGENT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encontró el archivo .env en $AGENT_DIR"
    echo "   Crea el archivo .env copiando .env.example"
    exit 1
fi

ACTION="${1:-disable}"
MAX_REQUESTS="${2:-1000}"

case "$ACTION" in
    enable|true|on)
        ENABLE_VALUE="true"
        echo "✅ Habilitando rate limiting con límite de $MAX_REQUESTS solicitudes"
        ;;
    disable|false|off)
        ENABLE_VALUE="false"
        echo "✅ Deshabilitando rate limiting (límite configurado: $MAX_REQUESTS)"
        ;;
    *)
        echo "❌ Error: Acción inválida: $ACTION"
        echo "   Uso: $0 [enable|disable] [max_requests]"
        echo "   Ejemplos:"
        echo "     $0 disable        # Deshabilitar rate limiting"
        echo "     $0 enable 5       # Habilitar con límite de 5"
        echo "     $0 enable 50      # Habilitar con límite de 50"
        exit 1
        ;;
esac

# Actualizar o agregar ENABLE_RATE_LIMITING
if grep -q "^ENABLE_RATE_LIMITING=" "$ENV_FILE"; then
    sed -i '' "s/^ENABLE_RATE_LIMITING=.*/ENABLE_RATE_LIMITING=$ENABLE_VALUE/" "$ENV_FILE"
else
    echo "" >> "$ENV_FILE"
    echo "# Rate Limiting Configuration" >> "$ENV_FILE"
    echo "ENABLE_RATE_LIMITING=$ENABLE_VALUE" >> "$ENV_FILE"
fi

# Actualizar o agregar MAX_REQUESTS_PER_USER
if grep -q "^MAX_REQUESTS_PER_USER=" "$ENV_FILE"; then
    sed -i '' "s/^MAX_REQUESTS_PER_USER=.*/MAX_REQUESTS_PER_USER=$MAX_REQUESTS/" "$ENV_FILE"
else
    echo "MAX_REQUESTS_PER_USER=$MAX_REQUESTS" >> "$ENV_FILE"
fi

echo ""
echo "📋 Configuración actualizada en .env:"
grep -E "(ENABLE_RATE_LIMITING|MAX_REQUESTS_PER_USER)" "$ENV_FILE" | grep -v "^#"
echo ""
echo "⚠️  Recuerda reiniciar el agente para que los cambios surtan efecto"

