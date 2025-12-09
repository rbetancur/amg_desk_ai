# Comandos cURL para Todos los Endpoints

Esta guía contiene todos los comandos cURL para probar los endpoints del backend AGM Desk AI.

**Base URL**: `http://localhost:8000`  
**API Key** (para endpoints de acción): `dev-api-secret-key-12345`

---

## 🔐 Variables de Entorno

Antes de ejecutar los comandos, puedes definir estas variables:

```bash
export API_KEY="dev-api-secret-key-12345"
export BASE_URL="http://localhost:8000"
export JWT_TOKEN="tu-jwt-token-aqui"  # Para endpoints de Mesa de Servicio
```

---

## 📋 Endpoints Básicos

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

### Root

```bash
curl -X GET http://localhost:8000/
```

### Documentación Swagger

```bash
# Abrir en navegador
open http://localhost:8000/docs
```

---

## 🎯 Endpoints de Acción - Amerika

### 1. Generar Contraseña

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "generate_password"
  }'
```

**Con variable de entorno**:
```bash
curl -X POST ${BASE_URL}/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "user_id": "test_user",
    "action_type": "generate_password"
  }'
```

### 2. Desbloquear Cuenta

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "unlock_account"
  }'
```

### 3. Bloquear Cuenta

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "lock_account"
  }'
```

**Alternativa con Authorization Bearer**:
```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "generate_password"
  }'
```

---

## 🏢 Endpoints de Acción - Dominio

### 1. Buscar Usuario

```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "find_user",
    "user_name": "mzuloaga"
  }'
```

**Buscar usuario que no existe** (contiene "test" o "demo"):
```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "find_user",
    "user_name": "test_user"
  }'
```

### 2. Cambiar Contraseña

```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "change_password"
  }'
```

### 3. Desbloquear Cuenta

```bash
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "unlock_account"
  }'
```

---

## 📝 Endpoints de Mesa de Servicio

**⚠️ IMPORTANTE**: Estos endpoints requieren un token JWT válido de Supabase.

### 1. Listar Solicitudes (con paginación)

```bash
curl -X GET "http://localhost:8000/api/requests?limit=50&offset=0" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Sin paginación** (usa valores por defecto):
```bash
curl -X GET http://localhost:8000/api/requests \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Con paginación personalizada**:
```bash
curl -X GET "http://localhost:8000/api/requests?limit=10&offset=0" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### 2. Crear Solicitud

**Categoría 300 - Cambio de Contraseña Cuenta Dominio**:
```bash
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codcategoria": 300,
    "description": "Necesito cambiar mi contraseña de dominio corporativo"
  }'
```

**Categoría 400 - Cambio de Contraseña Amerika**:
```bash
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codcategoria": 400,
    "description": "Necesito cambiar mi contraseña de la aplicación Amerika"
  }'
```

### 3. Obtener Solicitud Específica

```bash
# Reemplazar {id} con el ID de la solicitud (ej: 1, 2, 3...)
curl -X GET http://localhost:8000/api/requests/1 \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### 4. Actualizar Solicitud

**Actualizar estado a "En Trámite" (2)**:
```bash
curl -X PATCH http://localhost:8000/api/requests/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codestado": 2
  }'
```

**Actualizar estado a "Solucionado" (3) con solución**:
```bash
curl -X PATCH http://localhost:8000/api/requests/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codestado": 3,
    "solucion": "Contraseña cambiada exitosamente. Nueva contraseña: Abc123!@#",
    "fesolucion": "2024-01-15T10:30:00Z",
    "codusolucion": "AGENTE-MS"
  }'
```

**Actualizar con datos de clasificación de IA**:
```bash
curl -X PATCH http://localhost:8000/api/requests/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "ai_classification_data": {
      "app_type": "dominio",
      "confidence": 0.95,
      "classification_timestamp": "2024-01-15T10:30:00Z",
      "detected_actions": ["change_password", "unlock_account"],
      "raw_classification": "El usuario necesita cambiar su contraseña de dominio"
    }
  }'
```

---

## 🧪 Ejemplos de Pruebas Completas

### Flujo Completo: Crear y Actualizar Solicitud

```bash
# 1. Crear solicitud
RESPONSE=$(curl -s -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codcategoria": 300,
    "description": "Necesito cambiar mi contraseña de dominio"
  }')

# Extraer ID de la solicitud creada
REQUEST_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['codpeticiones'])")

echo "Solicitud creada con ID: $REQUEST_ID"

# 2. Obtener la solicitud
curl -X GET http://localhost:8000/api/requests/${REQUEST_ID} \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 3. Actualizar estado
curl -X PATCH http://localhost:8000/api/requests/${REQUEST_ID} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codestado": 2
  }'
```

### Probar Todos los Endpoints de Acción

```bash
# Amerika - Generar contraseña
echo "=== Amerika - Generar Contraseña ==="
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{"user_id": "test_user", "action_type": "generate_password"}' | python3 -m json.tool

# Dominio - Buscar usuario
echo -e "\n=== Dominio - Buscar Usuario ==="
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{"user_id": "test_user", "action_type": "find_user", "user_name": "mzuloaga"}' | python3 -m json.tool

# Dominio - Cambiar contraseña
echo -e "\n=== Dominio - Cambiar Contraseña ==="
curl -X POST http://localhost:8000/api/apps/dominio/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{"user_id": "test_user", "action_type": "change_password"}' | python3 -m json.tool
```

---

## ❌ Ejemplos de Errores

### Error 401 - API Key Inválida

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clave-incorrecta" \
  -d '{
    "user_id": "test_user",
    "action_type": "generate_password"
  }'
```

### Error 400 - Action Type Inválido

```bash
curl -X POST http://localhost:8000/api/apps/amerika/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-secret-key-12345" \
  -d '{
    "user_id": "test_user",
    "action_type": "invalid_action"
  }'
```

### Error 401 - Token JWT Faltante

```bash
curl -X GET http://localhost:8000/api/requests
```

### Error 422 - Categoría No Existe

```bash
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "codcategoria": 999,
    "description": "Categoría que no existe"
  }'
```

---

## 📊 Formatear Respuestas JSON

Para ver las respuestas formateadas, puedes usar:

```bash
# Con python
curl ... | python3 -m json.tool

# Con jq (si está instalado)
curl ... | jq

# Con python y colores (si tienes pygments)
curl ... | python3 -m json.tool | pygmentize -l json
```

---

## 🔍 Verificar Estado del Servidor

```bash
# Health check
curl http://localhost:8000/health | python3 -m json.tool

# Ver todas las rutas disponibles
curl http://localhost:8000/openapi.json | python3 -c "import sys, json; data = json.load(sys.stdin); [print(path) for path in data.get('paths', {}).keys()]"
```

---

## 📝 Notas

1. **API Key**: Los endpoints de acción (`/api/apps/*`) requieren la API Key configurada en `.env` como `API_SECRET_KEY`.

2. **JWT Token**: Los endpoints de Mesa de Servicio (`/api/requests/*`) requieren un token JWT válido de Supabase. Para obtener uno:
   - Usa el frontend de Supabase
   - O genera uno manualmente usando la `SUPABASE_ANON_KEY`

3. **Categorías Válidas**:
   - `300`: Cambio de Contraseña Cuenta Dominio
   - `400`: Cambio de Contraseña Amerika

4. **Estados de Solicitud**:
   - `1`: Pendiente
   - `2`: En Trámite
   - `3`: Solucionado

5. **Paginación**: Los límites por defecto son `limit=50` y `offset=0`. El máximo permitido es `limit=100`.

