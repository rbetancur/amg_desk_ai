# Plan de Implementación de la Mesa de Servicio Automatizada (Fase 1: Simulación)

Contexto General: La Fase 1 busca construir la funcionalidad mínima viable (PoC) del sistema, centrándose en la persistencia de datos y la orquestación en tiempo real a través de Supabase y FastAPI/React.

## PASO 1. Modelo de Datos y Configuración de Supabase (Equipo de Datos/DevOps)

"Definir y configurar el modelo de datos en Supabase (PostgreSQL) y habilitar la funcionalidad de Realtime para la orquestación del Agente AI. Se debe priorizar la seguridad con RLS y la autenticación centralizada. **IMPORTANTE**: Las tablas deben mantener los nombres legacy en español para garantizar retrocompatibilidad con el sistema existente."

Tareas Específicas:

1. **Modelo de Datos - Tabla HLP_CATEGORIAS**: Crear la tabla de categorías con los siguientes campos:
   - CODCATEGORIA (INTEGER, NOT NULL, PK)
   - CATEGORIA (VARCHAR(50), NOT NULL)

   **Valores iniciales**:
   - CODCATEGORIA: 300, CATEGORIA: "Cambio de Contraseña Cuenta Dominio"
   - CODCATEGORIA: 400, CATEGORIA: "Cambio de Contraseña Amerika"

2. **Modelo de Datos - Tabla HLP_PETICIONES**: Crear la tabla principal de solicitudes con los siguientes campos, asegurando tipos de datos apropiados y restricciones:

   **Campos Legacy (Retrocompatibilidad)**:
   - CODPETICIONES (BIGSERIAL o INTEGER, NOT NULL, PK) - Código de la solicitud
   - CODCATEGORIA (INTEGER, NOT NULL, FK a HLP_CATEGORIAS) - Categoría de la solicitud
   - CODESTADO (SMALLINT, NULL, valores: 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO, default: 1)
   - CODPRIORIDAD (SMALLINT, NULL, default: 3-ALTA)
   - CODGRAVEDAD (SMALLINT, NULL, default: 2-NORMAL)
   - CODFRECUENCIA (SMALLINT, NULL, default: 3-MUY FRECUENTE)
   - USUSOLICITA (VARCHAR(25), NOT NULL) - Código de usuario que registra la solicitud
   - FESOLICITA (TIMESTAMPTZ, NOT NULL, default: NOW()) - Fecha y hora de registro
   - DESCRIPTION (TEXT, NOT NULL) - Descripción del problema ingresada por el usuario
   - SOLUCION (TEXT, NULL) - Respuesta que llega al usuario final (se completa al resolver)
   - FESOLUCION (TIMESTAMPTZ, NULL) - Fecha y hora de solución
   - CODUSOLUCION (VARCHAR(24), NULL) - Código del usuario/agente que cierra la solicitud (ej: 'AGENTE-MS')
   - CODGRUPO (INTEGER, NULL, default: 4) - Grupo de atención (4 = I - Inmediata)
   - OPORTUNA (CHAR(1), NULL, default: 'X')
   - FECCIERRE (TIMESTAMPTZ, NULL) - Fecha y hora de cierre
   - CODMOTCIERRE (INTEGER, NULL, default: 5) - Motivo de cierre (5 = Respuesta Final)

   **Campo Adicional (Único nuevo para el sistema)**:
   - AI_CLASSIFICATION_DATA (JSONB, NULL) - Datos de auditoría de la IA (clasificación, confianza, tipo de aplicación detectada, etc.)

   **Notas importantes**:
   - Se mantienen EXACTAMENTE los campos legacy definidos en el esquema existente
   - `USUSOLICITA` debe obtenerse del usuario autenticado de Supabase: se extrae el username del email (parte antes de `@`). Ejemplo: `mzuloaga@aguasdemanizales.com.co` → `USUSOLICITA = "mzuloaga"`
   - `CODUSOLUCION` será 'AGENTE-MS' cuando el Agente AI resuelva automáticamente
   - `SOLUCION` contendrá la respuesta formal al usuario final (incluyendo contraseñas generadas si aplica)
   - `DESCRIPTION` contiene la descripción original del problema ingresada por el usuario
   - La clasificación del tipo de aplicación ('Amerika' o 'Dominio') se almacenará dentro de `AI_CLASSIFICATION_DATA` como JSONB
   - El estado se maneja mediante `CODESTADO` (1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO)

3. **Modelo de Datos - Tabla HLP_DOCUMENTACION** (Opcional para Fase 1): Crear la tabla de documentación técnica si se requiere en esta fase:
   - CODDOCUMENTACION (INTEGER, NOT NULL, PK)
   - CODPETICIONES (INTEGER, NOT NULL, FK a HLP_PETICIONES)
   - REQUERIMIENTO (TEXT) - Documentación técnica de la solución

4. **Configuración de Autenticación**: Habilitar la autenticación de Supabase (por ejemplo, con Email/Contraseña).

5. **Habilitación de Realtime**: Habilitar la replicación (Realtime) para la tabla `HLP_PETICIONES` para capturar eventos de INSERT. Esto permitirá que el Agente AI detecte nuevas solicitudes en tiempo real.

6. **Políticas de Seguridad (RLS)**: Implementar políticas de Row Level Security:
   - En `HLP_PETICIONES`: Los usuarios solo pueden ver/editar las solicitudes donde `USUSOLICITA` coincide con su username extraído del email (parte antes de `@`, ej: `mzuloaga` de `mzuloaga@aguasdemanizales.com.co`)
   - Las políticas RLS usan la función `get_username_from_auth_user()` que extrae el username del email del usuario autenticado
   - El Agente AI (usando service_role_key) debe tener acceso completo para leer y actualizar todas las solicitudes
   - Considerar políticas adicionales según los requisitos de auditoría y reportes
   - Ver documentación detallada en `agm-simulated-enviroment/backend/docs/DATABASE_SETUP.md` sección 7

7. **Claves de Acceso**: Generar y almacenar de forma segura la `service_role_key` de Supabase para el uso exclusivo del Agente AI. Esta clave permite al agente:
   - Leer todas las solicitudes (necesario para procesar nuevas solicitudes)
   - Actualizar solicitudes (para cambiar estado, agregar solution_log, etc.)
   - Bypass RLS cuando sea necesario para operaciones del sistema

8. **Mapeo de Nomenclatura**: Documentar el mapeo entre nombres legacy (español) en la BD y nombres modernos (inglés) en el código:
   - `HLP_PETICIONES` → `requests` o `petitions` en modelos de código
   - `HLP_CATEGORIAS` → `categories` en modelos de código
   - Los ORMs (SQLAlchemy para Python, TypeORM para TypeScript) deben configurarse con mapeo explícito de nombres de tabla

   **Documentación completa**: Ver [docs/NAMING_MAPPING.md](../docs/NAMING_MAPPING.md) para el mapeo detallado de tablas, campos, estados y convenciones.

## PASO 2. Backend Unificado (FastAPI) (Equipo Backend)

"Desarrollar el Backend Unificado usando FastAPI. Este servicio debe validar la autenticación de Supabase y exponer los endpoints de acción que serán consumidos por el Agente AI."

**Nota**: Para la especificación técnica detallada de este paso, incluyendo todas las tareas específicas, arquitectura, endpoints, autenticación, validaciones y orden de implementación, consulta el documento:

👉 **[Especificación Detallada: Backend Unificado (FastAPI)](./03_backend_detailed.md)**

El documento detallado incluye:

- **Fase 1**: Endpoints de Acción Simulados (Amerika y Dominio) - Implementación prioritaria
- **Fase 2**: Autenticación JWT de Supabase
- **Fase 3**: Endpoints CRUD de Mesa de Servicio
- **Fase 4**: Validaciones y Manejo de Errores
- **Fase 5**: Documentación y Testing

Cada fase contiene objetivos, tareas específicas, archivos a modificar/crear y notas de implementación.

## PASO 3. Frontend de Mesa de Servicio (React) (Equipo Frontend)

"Desarrollar una interfaz de usuario mínima en React para registrar solicitudes y visualizar su estado en tiempo real. La interfaz debe usar el SDK de Supabase para manejar la autenticación y la interacción inicial con los datos."

**Nota**: Para la especificación técnica detallada de este paso, incluyendo todas las tareas específicas, arquitectura, componentes, integración con Supabase Realtime, validaciones y orden de implementación, consulta el documento:

👉 **[Especificación Detallada: Frontend de Mesa de Servicio (React)](./04_frontend_detailed.md)**

El documento detallado incluye:

- **Fase 1**: Configuración del Proyecto y Setup - Establecer estructura base
- **Fase 2**: Autenticación con Supabase - Login/Registro y gestión de sesión
- **Fase 3**: Formulario de Solicitudes - Crear nuevas solicitudes
- **Fase 4**: Visualización de Solicitudes con Realtime - Tabla y actualizaciones en tiempo real
- **Fase 5**: Validaciones y Manejo de Errores - Robustez y experiencia de usuario

Cada fase contiene objetivos, tareas específicas, archivos a modificar/crear y notas de implementación.

## PASO 4. Agente AI (Orquestador) (Equipo Backend/AI)

"Desarrollar el Agente AI (Orquestador) que escucha eventos Realtime de Supabase, procesa solicitudes con Gemini AI, ejecuta acciones en el backend FastAPI y actualiza las solicitudes en la base de datos."

**Nota**: Para la especificación técnica detallada de este paso, incluyendo todas las tareas específicas, arquitectura, integración con Gemini AI, Supabase Realtime, ejecución de acciones y orden de implementación, consulta el documento:

👉 **[Especificación Detallada: Agente AI (Orquestador)](./05_agent_ai_detailed.md)**

El documento detallado incluye:

- **Fase 1**: Configuración del Proyecto y Setup - Establecer estructura base
- **Fase 2**: Ejecutor de Acciones - Integración con backend FastAPI
- **Fase 3**: Procesamiento con Gemini AI - Clasificación de solicitudes
- **Fase 4**: Listener de Realtime - Suscripción a eventos de Supabase
- **Fase 5**: Punto de Entrada y Orquestación - Integración completa

Cada fase contiene objetivos, tareas específicas, archivos a modificar/crear y notas de implementación.
