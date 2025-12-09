# AGM Desk AI

Sistema automatizado de atención a mesas de servicio para gestión de accesos corporativos.

## Descripción

AGM Desk AI es una solución de automatización diseñada para optimizar y agilizar el proceso de atención de solicitudes relacionadas con cuentas de acceso corporativas. El sistema automatiza el flujo completo que actualmente requiere intervención manual de una auxiliar, desde la interpretación de la solicitud hasta la ejecución de acciones técnicas y la comunicación con el funcionario.

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

-Documentación automática de acciones realizadas
-Registro de APIs utilizadas y resultados obtenidos
-Generación de mensajes formales para el funcionario
-Actualización automática del estado de la mesa de servicio
-Envío automático de notificaciones por correo electrónico

## Flujo del sistema

Para una descripción detallada del flujo actual y el proceso que el sistema automatiza, consulta [flujo actual.md](./flujo%20actual.md).

## Stack tecnológico

| Componente                         | Rol                                                                                     | Tecnología Principal          | Despliegue Sugerido      |
|-----------------------------------|------------------------------------------------------------------------------------------|-------------------------------|---------------------------|
| Núcleo de Datos / BaaS            | Base de datos única (PostgreSQL), APIs, Autenticación centralizada, Realtime (WebSockets). | Supabase                      | Plataforma Supabase       |
| Proyecto Unificado (Backend)      | Servidor de lógica de negocio, aloja los endpoints de Mesa de Servicio, América y Dominio. | Python (FastAPI)              | Railway                   |
| Proyecto Unificado (Frontend)     | Interfaz de Mesa de Servicio para el registro de solicitudes.                            | React                         | Vercel                    |
| Agente AI (Orquestador)           | Procesa solicitudes en tiempo real, clasifica, llama a endpoints de acción y actualiza la BD. | Python Script / FastAPI Listener | Railway                |

## Estructura del proyecto

El proyecto está organizado en tres componentes principales:

1. **Backend Unificado (FastAPI)**: Servidor monolítico modular que maneja la Mesa de Servicio y los endpoints simulados de AmeriKa y Dominio. Utiliza `pyproject.toml` para gestión de dependencias y está estructurado con separación modular (routers, models, services, core, db).

2. **Frontend React**: Interfaz de usuario para la Mesa de Servicio, organizada con principios de modularidad y custom hooks para facilitar la migración. Incluye una capa de abstracción de APIs (`api_services/`) que es crucial para la migración futura.

3. **Agente AI**: Servicio consumidor y orquestador independiente que procesa solicitudes en tiempo real mediante Supabase Realtime. Utiliza `pyproject.toml` para gestión de dependencias y está estructurado con separación modular (core, services).

### Estructura del Backend Unificado (agm-simulated-enviroment/backend/)

Aquí reside el FastAPI Monolítico Modular, que maneja tanto la Mesa de Servicio como los endpoints simulados de América y Dominio.

```agm-simulated-enviroment/
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Instancia principal de FastAPI
│   ├── core/                      # Configuración centralizada
│   │   ├── __init__.py
│   │   └── config.py              # Settings con pydantic-settings
│   ├── db/                        # Configuración de base de datos
│   │   ├── __init__.py
│   │   └── base.py                # SQLAlchemy engine, SessionLocal, Base
│   ├── routers/                   # Routers (Separación modular)
│   │   ├── __init__.py
│   │   ├── service_desk.py        # Rutas CRUD para solicitudes
│   │   ├── app_amerika.py         # Rutas de acción: /api/apps/amerika/...
│   │   └── app_domain.py          # Rutas de acción: /api/apps/domain/...
│   ├── models/                    # Modelos SQLAlchemy y Pydantic
│   │   ├── __init__.py
│   │   ├── entities.py            # Modelos SQLAlchemy (Category, Request)
│   │   └── schemas.py             # Esquemas Pydantic para validación
│   └── services/                  # Lógica de negocio e interacción con Supabase
│       ├── __init__.py
│       ├── supabase_service.py    # Lógica de conexión a Supabase
│       └── auth_service.py        # Lógica para validar JWT de Supabase
├── alembic/                       # Migraciones de base de datos
│   ├── versions/                  # Archivos de migración
│   │   └── 001_initial_migration.py
│   ├── env.py                     # Configuración de Alembic
│   └── script.py.mako             # Template para migraciones
├── scripts/                       # Scripts de utilidad
│   ├── setup-db.sh                # Configurar base de datos (local o Supabase)
│   ├── check-db.sh                # Verificar conexión y estado de BD
│   ├── run-migrations.sh          # Ejecutar migraciones de Alembic
│   └── verify-tables.py           # Verificar tablas creadas (Python)
├── docs/                          # Documentación
│   ├── DATABASE_SETUP.md          # Guía completa de configuración de BD
│   └── VERIFY_MIGRATIONS.md       # Guía para verificar migraciones
├── pyproject.toml                 # Dependencias y configuración del proyecto
├── docker-compose.yml              # Configuración de PostgreSQL local
├── alembic.ini                     # Configuración de Alembic
├── .env.example                   # Ejemplo de variables de entorno
└── .gitignore                     # Archivos a ignorar en git
```

### Estructura del Frontend (agm-simulated-enviroment/frontend/)

Esta estructura sigue los principios de modularidad y custom hooks para facilitar la migración.

```agm-simulated-enviroment/frontend/
├── src/
│   ├── api_services/        # Capa de Abstracción de APIs (crucial para migración)
│   │   ├── supabase_client.ts
│   │   ├── requests.ts      # Funciones para CRUD de solicitudes (getRequests, createRequest)
│   │   └── auth.ts          # Funciones específicas de autenticación que envuelven el cliente de Supabase
│   ├── assets/              # Recursos Estáticos
│   │   ├── images/          # Logos, iconos y otras imágenes
│   │   └── styles/          # Archivo principal de Tailwind CSS, fuentes personalizadas si las hay
│   ├── components/          # Componentes Reutilizables (UI)
│   │   ├── ui/              # Elementos de interfaz genéricos de Tailwind (Botón, Input, Modal)
│   │   └── layout/          # Componentes de diseño (Header, Sidebar, Footer)
│   ├── contexts/            # Contextos Globales (State Management)
│   │   └── AuthContext.tsx  # Para gestionar el estado de usuario autenticado
│   ├── features/            # Lógica de Negocio/Módulos
│   │   ├── requests/        # Módulo completo de la Mesa de Servicio
│   │   │   ├── RequestForm.tsx    # Componente que usa api_services/requests.ts para crear una solicitud
│   │   │   └── RequestTable.tsx   # Componente que usa el hook de datos para mostrar la tabla
│   │   └── auth/            # Lógica de login y signup
│   │       └── LoginForm.tsx
│   ├── hooks/               # Custom Hooks reutilizables
│   │   ├── useSupabaseAuth.ts    # Hook para obtener el estado de autenticación del usuario
│   │   └── useFetchRequests.ts   # Hook para obtener la lista de solicitudes del servidor
│   ├── lib/                 # Utilidades (Configuración, Helpers)
│   │   ├── constants.ts          # Constantes de la aplicación (ej. tipos de solicitud: 'América', 'Dominio')
│   │   └── validation_schemas.ts # Esquemas de validación de Zod/Yup utilizados en el frontend
│   └── pages/               # Rutas de la Aplicación
│       ├── HomePage.tsx
│       ├── Dashboard.tsx
│       └── LoginPage.tsx
└── package.json
```

**Descripción detallada de carpetas del Frontend:**

1. **api_services/** (La Clave de la Migración): Capa crucial para la migración. Contiene la lógica de comunicación con el backend, abstraída de los componentes.
   - `supabase_client.ts`: Configuración e inicialización del cliente de Supabase.
   - `requests.ts`: Funciones para CRUD de solicitudes (getRequests, createRequest).
   - `auth.ts`: Funciones específicas de autenticación que envuelven el cliente de Supabase.

2. **assets/**: Almacena todos los recursos estáticos.
   - `images/`: Logos, iconos y otras imágenes.
   - `styles/`: Archivo principal de Tailwind CSS, fuentes personalizadas si las hay.

3. **components/** (Componentes Reutilizables): Contiene componentes "tontos" (dumb) o de presentación. No tienen lógica de backend ni gestionan el estado global; solo reciben datos vía props y renderizan la UI.
   - `ui/`: Elementos de interfaz genéricos de Tailwind (Botón, Input, Modal).
   - `layout/`: Componentes de diseño (Header, Sidebar, Footer).

4. **contexts/** (Gestión de Estado Global): Si necesitas un estado accesible globalmente (mejor si se evita en favor de hooks y estado local).
   - `AuthContext.tsx`: Para gestionar el estado de usuario autenticado.

5. **features/** (Módulos de Funcionalidad Principal): Contiene la lógica de negocio de la aplicación. Estos son componentes "inteligentes" (smart) que usan hooks y servicios para interactuar con los datos.
   - `requests/`: Módulo completo de la Mesa de Servicio.
     - `RequestForm.tsx`: Componente que usa api_services/requests.ts para crear una solicitud.
     - `RequestTable.tsx`: Componente que usa el hook de datos para mostrar la tabla.
   - `auth/`: Lógica de login y signup.
     - `LoginForm.tsx`

6. **hooks/** (Lógica Reutilizable): Contiene todos los Custom Hooks que encapsulan lógica compleja o repetitiva.
   - `useSupabaseAuth.ts`: Hook para obtener el estado de autenticación del usuario.
   - `useFetchRequests.ts`: Hook para obtener la lista de solicitudes del servidor.

7. **lib/** (Utilidades): Contiene funciones helper genéricas, configuraciones y librerías externas.
   - `constants.ts`: Constantes de la aplicación (ej. tipos de solicitud: 'Amerika', 'Dominio').
   - `validation_schemas.ts`: Esquemas de validación de Zod/Yup utilizados en el frontend.

8. **pages/** (Rutas de la Aplicación): Corresponde a las rutas principales de tu aplicación (si usas React Router o Next.js/Gatsby). Actúan como contenedores de alto nivel para los componentes de features/.
   - `HomePage.tsx`
   - `Dashboard.tsx`
   - `LoginPage.tsx`

### Estructura del Agente AI (agm-desk-ai/)

Este es el servicio consumidor y orquestador que se ejecuta de forma independiente.

```agm-desk-ai/
├── agent/
│   ├── __init__.py
│   ├── main.py                    # Lógica principal del "Listener"
│   ├── core/                      # Configuración centralizada
│   │   ├── __init__.py
│   │   └── config.py              # Settings con pydantic-settings
│   └── services/                 # Servicios del agente
│       ├── __init__.py
│       ├── realtime_listener.py   # Suscripción a Supabase Realtime
│       ├── ai_processor.py        # Lógica de clasificación (Llamadas a Gemini)
│       └── action_executor.py     # Llama a los Endpoints de FastAPI simulados
├── pyproject.toml                 # Dependencias y configuración del proyecto
├── .env.example                   # Ejemplo de variables de entorno
└── .gitignore                     # Archivos a ignorar en git
```

## Entidades del Sistema

**Nota sobre Nomenclatura y Retrocompatibilidad:**

Las tablas de base de datos mantendrán los nombres legacy en español (ej: `HLP_CATEGORIAS`, `HLP_PETICIONES`) para garantizar retrocompatibilidad con el sistema existente. En el código de la aplicación se utilizarán nombres en inglés siguiendo estándares modernos de codificación, y los ORMs (SQLAlchemy, TypeORM) se configurarán para mapear automáticamente entre los nombres en inglés del código y los nombres en español de la base de datos.

**Estructura:**
-**Base de Datos**: Nombres legacy en español (sin cambios)
-**Código**: Nombres en inglés con estándares modernos
-**Mapeo**: Configuración explícita en modelos/ORM para traducción automática

### HLP_CATEGORIAS

-CODCATEGORIA (NUMBER(5), NOT NULL, Clave Primaria (PK))
-CATEGORIA (VARCHAR(50), NOT NULL)

#### VALORES INICIALES

```HLP_CATEGORIAS
{
  "HLP_CATEGORIAS": [
    {
      "CODCATEGORIA": 300,
      "CATEGORIA": "Cambio de Contraseña Cuenta Dominio"
    },
    {
      "CODCATEGORIA": 400,
      "CATEGORIA": "Cambio de Contraseña Amerika"
    }
  ]
}
```

### HLP_PETICIONES

-CODPETICIONES (NUMBER(8), NOT NULL, Clave Primaria (PK), DESCRIPCION: codigo de la solicitud)
-CODCATEGORIA (NUMBER(5), NOT NULL, Clave Foránea (FK), DESCRIPCION:Codigo de la categoria a la que pertenece la solicitud)
-CODESTADO (NUMBER(2), NULL, VALORES PERMITIDOS: 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO)
-CODPRIORIDAD (NUMBER(2), NULL, DEFECTO: 3-ALTA)
-CODGRAVEDAD (NUMBER(2), NULL, DEFECTO: 2-NORMAL)
-CODFRECUENCIA (NUMBER(2), NULL, DEFECTO: 3-MUY FRECUENTE)
-USUSOLICITA (VARCHAR2(25), NOT NULL, DESCRIPCION: CODIGO DE USUARIO QUIEN REGISTRA LA SOLICITUD, EJEMPLO: MZULOAGA)
-FESOLICITA (DATE, NOT NULL, DESCRIPCION: FECHA Y HORA EN QUE SE RTEGISTRA LA SOLICITUD)
-DESCRIPTION (VARCHAR2(4000), NOT NULL, DESCRIPCION: REQUERIMIENTOS PARA REALIZAR LA PETICION. ES EL TEXTO QUE INGRESA EL USUARIO)
-SOLUCION (VARCHAR(4000), NOT NULL, DESCRIPCION: para colocar la respuesta que le llega al  usuario final )
-FESOLUCION (DATE, NOT NULL, DESCRIPCION: FECHA Y HORA DE SOLUCION)
-CODUSOLUCION (VARCHAR2(24), NOT NULL, DESCRIPCION: CODIGO DEL USUARIO DE TI QUE CIERRA LA SOLICITUD. EJEMPLO: AGENTE-MS)
-CODGRUPO (NUMBER(5), NULL, DESCRIPCION: GRUPO DE ATENCION QUE IDENTIFICA EL TIPO DE ATENCION DE LA SOLICITUD, DEFECTO: 4 - I (Inmediata))
-OPORTUNA (CHAR(1), NULL, DEFECTO: 'X')
-FECCIERRE (DATE, NOT NULL, DESCRIPCION: FECHA Y HORA EN QUE SE CERRO LA SOLICITUD)
-CODMOTCIERRE (NUMBER(5), NULL, DESCRIPCION:ESTABLECE UN MOTIVO DE CIERRE, DEFECTO:  5-Respuesta Final)

request_id (UUID / SERIAL BIGINT)
user_id (UUID) - Clave Foránea (FK) al Usuario que creó la solicitud.
created_at (TIMESTAMPZ) - Fecha y hora de creación.
app_type (TEXT / ENUM) - Clasificación: 'América' o 'Dominio'.
request_details (TEXT) - Descripción original del problema.
status (TEXT / ENUM) - Estado: 'Pendiente', 'En Proceso', 'Resuelto', 'Fallo'.
solution_log (TEXT) - Bitácora generada por el Agente AI con el resultado.
ai_classification_data (JSONB) - Datos opcionales de auditoría de la IA.

### HLP_DOCUMENTACION

-CODDOCUMENTACION (NUMBER(5), NOT NULL)
-CODPETICIONES (NUMBER(8), NOT NULL, Clave Foránea(FK))
-REQUERIMIENTO (VARCHAR2(40000), DESCRIPCION:documentacion tecnica de la solucion)

## Política de contraseñas

### Para cuentas de dominio

-Deben usarse caracteres alfanuméricos
-Se deben usar mínimo 10 caracteres y tener letras mayúsculas, letras minúsculas, números y/o símbolos como: *.?!#&$.

### Para aplicación Amerika

-Contraseñas alfanuméricas
-Longitud mínimo 10 caracteres - máximo 25

## Estado del proyecto

En desarrollo - El sistema está siendo diseñado para automatizar completamente el flujo descrito en el documento de flujo actual.

## Scripts de Utilidad

El backend incluye varios scripts de utilidad para facilitar el desarrollo y la configuración:

### Scripts de Base de Datos

- **`scripts/setup-db.sh`**: Configura la base de datos (PostgreSQL local o Supabase)
  - Uso: `./scripts/setup-db.sh [local|supabase]`
  - Automatiza la configuración e instalación de dependencias

- **`scripts/check-db.sh`**: Verifica la conexión y estado de la base de datos
  - Uso: `./scripts/check-db.sh`
  - Detecta automáticamente si estás usando PostgreSQL local o Supabase

- **`scripts/run-migrations.sh`**: Ejecuta las migraciones de Alembic
  - Uso: `./scripts/run-migrations.sh`
  - Instala dependencias automáticamente si es necesario

- **`scripts/verify-tables.py`**: Script Python para verificar que las tablas se crearon correctamente
  - Uso: `python scripts/verify-tables.py`

### Documentación

- **`docs/DATABASE_SETUP.md`**: Guía completa de configuración de base de datos
  - Instrucciones para PostgreSQL local y Supabase
  - Configuración de Realtime y RLS
  - Troubleshooting

- **`docs/VERIFY_MIGRATIONS.md`**: Guía rápida para verificar migraciones
  - Múltiples métodos de verificación
  - Soluciones rápidas a problemas comunes

## Notas importantes

- El sistema está diseñado para manejar únicamente solicitudes de cambio de contraseña y desbloqueo de cuentas
- Las operaciones de bloqueo de cuentas o procesamiento de novedades están fuera del alcance inicial del agente
- El sistema debe mantener la seguridad y confidencialidad de las credenciales generadas
- Se debe mantener un enfoque simple  y funcional sobre el core de la solución si features adicionales complejas
