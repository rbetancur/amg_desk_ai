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
   - `USUSOLICITA` debe obtenerse del usuario autenticado de Supabase (puede mapearse desde el email o metadata del usuario)
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
   - En `HLP_PETICIONES`: Los usuarios solo pueden ver/editar las solicitudes donde `USUSOLICITA` coincide con su código de usuario (obtenido de `auth.users` metadata o email)
   - El Agente AI (usando service_role_key) debe tener acceso completo para leer y actualizar todas las solicitudes
   - Considerar políticas adicionales según los requisitos de auditoría y reportes

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

Tareas Específicas:

1. Estructura del Proyecto: Inicializar el proyecto FastAPI y configurar el entorno Python.

2. Integración de Autenticación: Implementar la lógica para validar los JWTs emitidos por Supabase en las solicitudes a los endpoints críticos.

3. Endpoint de Mesa de Servicio (Controlador CRUD): Implementar los endpoints básicos de la API para que el Frontend pueda insertar y consultar solicitudes en la tabla `HLP_PETICIONES` de Supabase. Los endpoints deben:
   - Mapear entre los nombres legacy de la BD (español) y los nombres modernos en el código (inglés)
   - Validar que el usuario autenticado del JWT coincida con `USUSOLICITA` (obtenido del email o metadata del usuario)
   - Manejar la conversión entre estados numéricos legacy (CODESTADO: 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO) y estados textuales modernos para la UI ('Pendiente', 'En Trámite', 'Solucionado')
   - Usar los campos legacy existentes: `DESCRIPTION` para la descripción del problema, `SOLUCION` para la respuesta al usuario, `FESOLICITA` para fecha de creación, etc.

4. Endpoints de Acción: Implementar los endpoints simulados que el Agente AI llamará. Estos deben estar protegidos con un token o clave API secreta dedicada.

    - POST /api/apps/amerika/execute-action (Acepta user_id, action_type)
    - POST /api/apps/dominio/execute-action (Acepta user_id, action_type)

5. Simulación de Lógica Externa: Dentro de los endpoints de Acción (Tarea 4), incluir una lógica simple de simulación (e.g., un sleep de 2 segundos para simular el procesamiento y un log de la acción realizada) para devolver una respuesta de éxito o fracaso.

## PASO 3. Frontend de Mesa de Servicio (React) (Equipo Frontend)

"Desarrollar una interfaz de usuario mínima en React para registrar solicitudes y visualizar su estado en tiempo real. La interfaz debe usar el SDK de Supabase para manejar la autenticación y la interacción inicial con los datos."

Tareas Específicas:

1. Configuración del Proyecto: Inicializar el proyecto React y configurar el SDK de Supabase para el frontend.

2. Página de Autenticación: Implementar la interfaz de Login/Registro usando el cliente de autenticación de Supabase.

3. Formulario de Solicitud: Crear un formulario simple para registrar una nueva solicitud. Debe capturar:
    - CODCATEGORIA (selección de categoría: 300 o 400, o permitir que el usuario seleccione de HLP_CATEGORIAS)
    - DESCRIPTION (Descripción del problema ingresada por el usuario)
    - El campo `USUSOLICITA` debe derivarse del email o metadata del usuario autenticado (obtenido del JWT de Supabase) antes de insertar el registro en `HLP_PETICIONES`
    - `FESOLICITA` se establecerá automáticamente con la fecha/hora actual al crear el registro

4. Visualización de Solicitudes: Implementar una tabla o lista que muestre las solicitudes creadas por el usuario logeado, mostrando:
    - CODESTADO (convertido a texto legible: Pendiente, En Trámite, Solucionado)
    - DESCRIPTION (descripción del problema)
    - SOLUCION (respuesta al usuario final cuando esté disponible)
    - FESOLICITA (fecha de creación)
    - FESOLUCION (fecha de solución, si aplica)
    - AI_CLASSIFICATION_DATA (opcionalmente mostrar información de clasificación de la IA si está disponible)

## Siguiente Paso

Una vez completadas estas tareas, el siguiente paso será desarrollar el Agente AI (Orquestador) para cerrar el ciclo de automatización.
