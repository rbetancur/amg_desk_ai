# Configuración de Variables de Entorno

Este documento explica cómo configurar las variables de entorno para el Agente AI, especialmente para controlar el rate limiting durante pruebas.

## Archivos

- `.env.example`: Plantilla con todas las variables disponibles (puede subirse al repositorio)
- `.env`: Tu archivo de configuración real (NO se sube al repositorio, está en .gitignore)

## Configuración de Rate Limiting

### Para Deshabilitar Rate Limiting (Pruebas)

Edita tu archivo `.env` y agrega o modifica estas líneas:

```env
# Rate Limiting Configuration - PRUEBAS
ENABLE_RATE_LIMITING=false
MAX_REQUESTS_PER_USER=1000
RATE_LIMIT_WINDOW_HOURS=24
```

### Para Habilitar Rate Limiting (Producción)

```env
# Rate Limiting Configuration - PRODUCCIÓN
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_USER=5
RATE_LIMIT_WINDOW_HOURS=24
```

### Para Ajustar el Límite sin Deshabilitar

```env
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_USER=50  # Aumenta el límite a 50 solicitudes
RATE_LIMIT_WINDOW_HOURS=24
```

## Variables Disponibles

### Rate Limiting

- `ENABLE_RATE_LIMITING` (bool): `true` para habilitar, `false` para deshabilitar
- `MAX_REQUESTS_PER_USER` (int): Número máximo de solicitudes por usuario en la ventana de tiempo
- `RATE_LIMIT_WINDOW_HOURS` (int): Ventana de tiempo en horas para contar solicitudes (ej: 24 = últimas 24 horas)
- `MAX_REQUEST_AGE_HOURS` (int, opcional): Si está configurado, rechaza solicitudes más antiguas que este valor

### Otras Variables Importantes

Consulta el archivo `.env.example` para ver todas las variables disponibles.

## Notas

1. **No modifiques el código**: Todos los cambios se hacen en el archivo `.env`
2. **Reinicia el agente**: Después de cambiar variables en `.env`, reinicia el agente para que tome los nuevos valores
3. **Valores por defecto**: Si una variable no está en `.env`, se usan los valores por defecto definidos en `config.py`

## Ejemplo Rápido

Para deshabilitar rate limiting durante pruebas:

```bash
cd agm-desk-ai
# Edita .env y agrega:
echo "ENABLE_RATE_LIMITING=false" >> .env
echo "MAX_REQUESTS_PER_USER=1000" >> .env
```

Luego reinicia el agente.

