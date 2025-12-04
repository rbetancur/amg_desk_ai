# AMG Desk AI

Sistema automatizado de atención a mesas de servicio para gestión de accesos corporativos.

## Descripción

AMG Desk AI es una solución de automatización diseñada para optimizar y agilizar el proceso de atención de solicitudes relacionadas con cuentas de acceso corporativas. El sistema automatiza el flujo completo que actualmente requiere intervención manual de una auxiliar, desde la interpretación de la solicitud hasta la ejecución de acciones técnicas y la comunicación con el funcionario.

## Problema que resuelve

Actualmente, el proceso de atención de mesas de servicio para gestión de accesos depende completamente de una auxiliar que debe:

- Interpretar manualmente cada mesa de servicio
- Validar y corregir la categorización de la solicitud
- Identificar el problema real a partir de la descripción del usuario
- Ejecutar acciones técnicas a través de múltiples APIs
- Documentar la resolución
- Comunicar el resultado al funcionario

Este proceso manual es propenso a errores, consume tiempo valioso y limita la capacidad de respuesta del equipo de soporte.

## Objetivo

Automatizar el flujo completo de atención de mesas de servicio para dos tipos de solicitudes principales:

1. **Cambio de contraseña**: Para cuentas de Dominio corporativo o aplicación Amerika
2. **Desbloqueo de cuenta**: Para cuentas de Dominio corporativo o aplicación Amerika

## Funcionalidades principales

### Gestión de solicitudes
- Recepción y análisis automático de mesas de servicio
- Validación y corrección automática de categorización
- Identificación inteligente del tipo de solicitud (cambio de contraseña, desbloqueo, o ambas)
- Determinación automática del tipo de cuenta afectada (Dominio o Amerika)

### Operaciones técnicas
- **Para cuentas de Dominio**:
  - Consulta de usuario por nombre de funcionario
  - Cambio de contraseña
  - Desbloqueo de cuenta
  - Integración con APIs del dominio corporativo

- **Para cuentas de Amerika**:
  - Generación de nueva contraseña
  - Bloqueo y desbloqueo de acceso
  - Integración con APIs específicas de Amerika

### Documentación y comunicación
- Documentación automática de acciones realizadas
- Registro de APIs utilizadas y resultados obtenidos
- Generación de mensajes formales para el funcionario
- Actualización automática del estado de la mesa de servicio
- Envío automático de notificaciones por correo electrónico

## Flujo del sistema

Para una descripción detallada del flujo actual y el proceso que el sistema automatiza, consulta [flujo actual.md](./flujo%20actual.md).

## Stack tecnológico

<!-- Esta sección será completada posteriormente con las tecnologías específicas utilizadas en el proyecto -->

## Estructura del proyecto

```
amg_desk_AI/
├── docs/
│   ├── README.md
│   └── flujo actual.md
└── ...
```

## Estado del proyecto

En desarrollo - El sistema está siendo diseñado para automatizar completamente el flujo descrito en el documento de flujo actual.

## Notas importantes

- El sistema está diseñado para manejar únicamente solicitudes de cambio de contraseña y desbloqueo de cuentas
- Las operaciones de bloqueo de cuentas o procesamiento de novedades están fuera del alcance inicial del agente
- El sistema debe mantener la seguridad y confidencialidad de las credenciales generadas
- Se debe mantener un enfoque simple  y funcional sobre el core de la solución si features adicionales complejas
