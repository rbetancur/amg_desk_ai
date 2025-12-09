# Especificación Detallada: Frontend de Mesa de Servicio (React)

Este documento detalla la implementación del Frontend de Mesa de Servicio usando React, expandiendo el Paso 3 del plan de desarrollo principal con especificaciones técnicas completas.

## Descripción

Desarrollar una interfaz de usuario mínima en React para registrar solicitudes y visualizar su estado en tiempo real. La interfaz debe usar el SDK de Supabase para manejar la autenticación y la interacción inicial con los datos.

**Contexto**: Este frontend es una aplicación React que permite a los usuarios autenticarse, crear solicitudes de mesa de servicio y visualizar el estado de sus solicitudes en tiempo real. Utiliza Supabase para autenticación y Realtime para actualizaciones automáticas.

**Referencias**:
- [Plan de Desarrollo Principal](./02_dev_plan.md#paso-3-frontend-de-mesa-de-servicio-react-equipo-frontend)
- [Estructura del Frontend](../docs/README.md#estructura-del-frontend-agm-simulated-enviromentfrontend)
- [Mapeo de Nomenclatura](../docs/NAMING_MAPPING.md)
- [Especificación del Backend](./03_backend_detailed.md)

---

## FASE 1: Configuración del Proyecto y Setup

**Justificación**: Establecer la estructura base del proyecto React con todas las herramientas y configuraciones necesarias antes de implementar funcionalidades específicas.

### 1.1. Inicialización del Proyecto React

**Objetivo**: Crear el proyecto React con TypeScript y configurar las herramientas de desarrollo.

**Tareas**:
1. Inicializar proyecto React con TypeScript usando Vite:
   ```bash
   npm create vite@latest . -- --template react-ts
   ```
   O usar el template apropiado según preferencias del equipo.

2. Configurar `package.json` con dependencias necesarias:
   - `react` y `react-dom` (versiones estables)
   - `typescript` y `@types/react`, `@types/react-dom`
   - `@supabase/supabase-js` (SDK de Supabase)
   - `react-router-dom` (para routing)
   - `zod` (validación de formularios)
   - `react-hook-form` (gestión de formularios)
   - `@hookform/resolvers` (integración Zod con react-hook-form)
   - `tailwindcss`, `postcss`, `autoprefixer` (estilos)
   - `date-fns` (formateo de fechas)
   - `lucide-react` (iconos modernos y elegantes - ver sección "Sistema de Iconos")

3. Crear estructura de carpetas según especificación:
   ```
   src/
   ├── api_services/
   ├── assets/
   │   ├── images/
   │   └── styles/
   ├── components/
   │   ├── ui/
   │   └── layout/
   ├── contexts/
   ├── features/
   │   ├── auth/
   │   └── requests/
   ├── hooks/
   ├── lib/
   └── pages/
   ```

4. Configurar TypeScript (`tsconfig.json`):
   - Habilitar strict mode
   - Configurar paths para imports absolutos (opcional)
   - Incluir tipos de React y DOM

5. Configurar Tailwind CSS:
   - Inicializar Tailwind: `npx tailwindcss init -p`
   - Configurar `tailwind.config.js` con paths de contenido
   - Crear archivo CSS principal en `src/assets/styles/index.css` con directivas de Tailwind

6. Configurar variables de entorno:
   - Crear `.env.example` con:
     ```
     VITE_SUPABASE_URL=https://[PROJECT-REF].supabase.co
     VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     VITE_BACKEND_URL=http://localhost:8000
     ```
   - Crear `.env.local` para desarrollo (no commiteado)
   - Documentar en README cómo configurar variables de entorno

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/package.json`
- `agm-simulated-enviroment/frontend/tsconfig.json`
- `agm-simulated-enviroment/frontend/tailwind.config.js`
- `agm-simulated-enviroment/frontend/postcss.config.js`
- `agm-simulated-enviroment/frontend/vite.config.ts` (o webpack.config.js según herramienta)
- `agm-simulated-enviroment/frontend/.env.example`
- `agm-simulated-enviroment/frontend/src/assets/styles/index.css`

### 1.2. Configuración del Cliente de Supabase

**Objetivo**: Configurar el cliente de Supabase para autenticación y acceso a datos.

**Tareas**:
1. Crear `src/api_services/supabase_client.ts`:
   - Importar `createClient` de `@supabase/supabase-js`
   - Obtener `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` de variables de entorno
   - Crear y exportar instancia del cliente:
     ```typescript
     import { createClient } from '@supabase/supabase-js'
     
     const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
     const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY
     
     if (!supabaseUrl || !supabaseAnonKey) {
       throw new Error('Missing Supabase environment variables')
     }
     
     export const supabase = createClient(supabaseUrl, supabaseAnonKey)
     ```
   - Validar que las variables de entorno estén presentes (lanzar error descriptivo si faltan)

2. Crear tipos TypeScript para datos de Supabase:
   - Crear `src/lib/types.ts` con interfaces:
     - `Request` (mapeo de HLP_PETICIONES)
     - `Category` (mapeo de HLP_CATEGORIAS)
     - `AIClassificationData` (estructura de ai_classification_data)
   - Usar nombres en inglés en el código (mapeo desde nombres legacy en BD)

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/api_services/supabase_client.ts`
- `agm-simulated-enviroment/frontend/src/lib/types.ts`

### 1.3. Configuración de Routing

**Objetivo**: Configurar React Router para navegación entre páginas.

**Tareas**:
1. Instalar y configurar `react-router-dom`
2. Crear componente `App.tsx` con rutas:
   - `/` → `HomePage` (redirige a Dashboard si autenticado, LoginPage si no)
   - `/login` → `LoginPage`
   - `/dashboard` → `Dashboard` (protegida, requiere autenticación)
3. Crear componente `ProtectedRoute` que:
   - Verifica si el usuario está autenticado usando Supabase
   - Redirige a `/login` si no está autenticado
   - Renderiza el componente hijo si está autenticado

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/App.tsx`
- `agm-simulated-enviroment/frontend/src/components/layout/ProtectedRoute.tsx`

---

## FASE 2: Autenticación con Supabase

**Justificación**: La autenticación es fundamental para todas las funcionalidades posteriores. Los usuarios deben poder iniciar sesión y registrarse antes de crear o ver solicitudes.

### 2.1. Servicio de Autenticación

**Objetivo**: Crear funciones reutilizables para autenticación usando el SDK de Supabase.

**Tareas**:
1. Crear `src/api_services/auth.ts` con funciones:
   - `signIn(email: string, password: string)`: Iniciar sesión
     - Usar `supabase.auth.signInWithPassword()`
     - Retornar `{ user, error }`
   - `signUp(email: string, password: string)`: Registrarse
     - Usar `supabase.auth.signUp()`
     - Retornar `{ user, error }`
   - `signOut()`: Cerrar sesión
     - Usar `supabase.auth.signOut()`
   - `getCurrentUser()`: Obtener usuario actual
     - Usar `supabase.auth.getUser()`
     - Retornar usuario o null
   - `getSession()`: Obtener sesión actual
     - Usar `supabase.auth.getSession()`
     - Retornar sesión o null

2. Crear helper `extractUsernameFromEmail(email: string): string`:
   - Extraer parte antes de `@` del email
   - Validar que no exceda 25 caracteres (lanzar error si excede)
   - Ejemplo: `mzuloaga@aguasdemanizales.com.co` → `"mzuloaga"`

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/api_services/auth.ts`

### 2.2. Contexto de Autenticación

**Objetivo**: Crear un contexto React para gestionar el estado de autenticación globalmente.

**Tareas**:
1. Crear `src/contexts/AuthContext.tsx`:
   - Crear contexto con `createContext`
   - Estado: `user`, `loading`, `error`
   - Funciones: `signIn`, `signUp`, `signOut`
   - Provider que:
     - Escucha cambios de autenticación con `supabase.auth.onAuthStateChange()`
     - Actualiza estado cuando usuario inicia/cierra sesión
     - Carga usuario inicial al montar

2. Crear hook `useAuth()`:
   - Hook personalizado que consume `AuthContext`
   - Retorna `{ user, loading, signIn, signUp, signOut }`
   - Lanza error si se usa fuera del Provider

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/contexts/AuthContext.tsx`

### 2.3. Hook de Autenticación

**Objetivo**: Crear hook personalizado para facilitar el uso de autenticación en componentes.

**Tareas**:
1. Crear `src/hooks/useSupabaseAuth.ts`:
   - Hook que envuelve `useAuth()` del contexto
   - Proporciona helpers adicionales:
     - `isAuthenticated: boolean`
     - `username: string | null` (extraído del email)
     - `getAuthToken(): Promise<string | null>` (obtener JWT para llamadas al backend)

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/hooks/useSupabaseAuth.ts`

### 2.4. Componente de Login

**Objetivo**: Implementar interfaz de Login/Registro.

**Tareas**:
1. Crear `src/features/auth/LoginForm.tsx`:
   - Formulario con campos: email, password
   - Toggle para cambiar entre Login y Registro
   - Validación con Zod:
     - Email: formato válido
     - Password: mínimo 6 caracteres (o según política de Supabase)
   - Usar `react-hook-form` con resolver de Zod
   - Manejo de errores:
     - Mostrar mensajes de error de Supabase de forma amigable
     - Estados de carga durante autenticación
   - Redirigir a `/dashboard` después de login exitoso

2. Crear `src/pages/LoginPage.tsx`:
   - Página que contiene `LoginForm`
   - Layout básico con Tailwind CSS
   - Redirigir a `/dashboard` si ya está autenticado

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/features/auth/LoginForm.tsx`
- `agm-simulated-enviroment/frontend/src/pages/LoginPage.tsx`
- `agm-simulated-enviroment/frontend/src/lib/validation_schemas.ts` (esquemas Zod para auth)

---

## FASE 3: Formulario de Solicitudes

**Justificación**: El formulario permite a los usuarios crear nuevas solicitudes. Es la funcionalidad principal de entrada de datos.

### 3.1. Servicio de Solicitudes

**Objetivo**: Crear funciones para interactuar con el backend (CRUD de solicitudes).

**Tareas**:
1. Crear `src/api_services/requests.ts` con funciones:
   - `createRequest(data: RequestCreate): Promise<Request>`:
     - Obtener token JWT del usuario autenticado
     - Llamar a `POST /api/requests` del backend
     - Headers: `Authorization: Bearer <token>`
     - Retornar solicitud creada
   - `getRequests(limit?: number, offset?: number): Promise<PaginatedResponse<Request>>`:
     - Obtener token JWT
     - Llamar a `GET /api/requests?limit=50&offset=0`
     - Retornar respuesta paginada
   - `getRequestById(id: number): Promise<Request>`:
     - Obtener token JWT
     - Llamar a `GET /api/requests/{id}`
     - Retornar solicitud
   - Helper `getAuthHeaders()`:
     - Obtener token JWT de Supabase
     - Retornar headers con `Authorization: Bearer <token>`
     - Manejar caso cuando no hay token (lanzar error)

2. Configurar URL base del backend:
   - Crear `src/lib/constants.ts`:
     - `BACKEND_URL` desde `VITE_BACKEND_URL` o default `http://localhost:8000`
     - Helper `getBackendUrl(endpoint: string): string`

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/api_services/requests.ts`
- `agm-simulated-enviroment/frontend/src/lib/constants.ts`

### 3.2. Esquemas de Validación

**Objetivo**: Definir esquemas Zod para validar datos del formulario.

**Tareas**:
1. Crear/actualizar `src/lib/validation_schemas.ts`:
   - `RequestCreateSchema`:
     - `codcategoria`: número, debe ser 300 o 400 (o validar contra categorías disponibles)
     - `description`: string, mínimo 1 carácter, máximo 4000 caracteres
   - `CategorySchema`:
     - `codcategoria`: número
     - `categoria`: string

2. Crear helper para obtener categorías:
   - Función `getCategories(): Promise<Category[]>`:
     - Llamar a endpoint del backend (si existe) o usar valores hardcodeados inicialmente
     - Categorías: 300 (Cambio de Contraseña Cuenta Dominio), 400 (Cambio de Contraseña Amerika)

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/lib/validation_schemas.ts`
- `agm-simulated-enviroment/frontend/src/lib/constants.ts` (agregar categorías)

### 3.3. Componente de Formulario

**Objetivo**: Implementar formulario para crear solicitudes.

**Tareas**:
1. Crear `src/features/requests/RequestForm.tsx`:
   - Formulario con campos:
     - Select de categoría (CODCATEGORIA):
       - Opciones: 300, 400 (o cargar desde backend)
       - Mostrar nombre legible de categoría
     - Textarea para descripción (DESCRIPTION):
       - Placeholder descriptivo
       - Validación en tiempo real
       - Contador de caracteres (máximo 4000)
   - Validación con `react-hook-form` + Zod
   - Estados:
     - `isSubmitting`: durante envío
     - `error`: mensaje de error si falla
     - `success`: confirmación de éxito
   - Al enviar:
     - Llamar a `createRequest()` de `api_services/requests.ts`
     - Mostrar mensaje de éxito
     - Limpiar formulario
     - Opcional: redirigir o actualizar lista de solicitudes
   - Notas importantes:
     - `USUSOLICITA` se deriva automáticamente del email del usuario autenticado (backend lo maneja)
     - `FESOLICITA` se establece automáticamente en el backend
     - El formulario solo envía `codcategoria` y `description`

2. Estilos con Tailwind CSS:
   - Diseño responsive (mobile-first)
   - Estados visuales: disabled, error, success
   - Accesibilidad: labels, aria-labels, focus states

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/features/requests/RequestForm.tsx`

---

## FASE 4: Visualización de Solicitudes con Realtime

**Justificación**: Los usuarios necesitan ver sus solicitudes y recibir actualizaciones en tiempo real cuando el Agente AI procesa y resuelve las solicitudes.

### 4.1. Hook para Obtener Solicitudes

**Objetivo**: Crear hook personalizado que obtiene y gestiona el estado de las solicitudes.

**Tareas**:
1. Crear `src/hooks/useFetchRequests.ts`:
   - Hook que:
     - Obtiene solicitudes usando `getRequests()` de `api_services/requests.ts`
     - Gestiona estados: `requests`, `loading`, `error`
     - Soporta paginación: `limit`, `offset`
     - Función `refetch()` para recargar datos
   - Implementación inicial sin Realtime (se agregará en 4.2)

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/hooks/useFetchRequests.ts`

### 4.2. Integración con Supabase Realtime

**Objetivo**: Suscribirse a cambios en tiempo real de la tabla HLP_PETICIONES.

**Tareas**:
1. Actualizar `src/hooks/useFetchRequests.ts`:
   - Agregar suscripción a Realtime usando `supabase.channel()`:
     ```typescript
     const channel = supabase
       .channel('requests-changes')
       .on(
         'postgres_changes',
         {
           event: '*', // INSERT, UPDATE, DELETE
           schema: 'public',
           table: 'HLP_PETICIONES',
           filter: `USUSOLICITA=eq.${username}` // Solo cambios del usuario
         },
         (payload) => {
           // Actualizar estado según tipo de evento
         }
       )
       .subscribe()
     ```
   - Manejar eventos:
     - `INSERT`: Agregar nueva solicitud a la lista
     - `UPDATE`: Actualizar solicitud existente (ej: cambio de estado, solución agregada)
     - `DELETE`: Remover solicitud de la lista (si aplica)
   - Limpiar suscripción en cleanup de `useEffect`
   - Validar que el usuario esté autenticado antes de suscribirse

2. Optimizaciones:
   - Evitar re-renders innecesarios usando `useMemo` y `useCallback`
   - Actualizar solo la solicitud afectada, no recargar toda la lista
   - Manejar casos edge: solicitud actualizada que no está en la lista actual (paginación)

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/hooks/useFetchRequests.ts`

### 4.3. Componente de Tabla de Solicitudes

**Objetivo**: Implementar tabla que muestra las solicitudes del usuario.

**Tareas**:
1. Crear `src/features/requests/RequestTable.tsx`:
   - Tabla que muestra columnas:
     - CODESTADO (convertido a texto: "Pendiente", "En Trámite", "Solucionado")
     - DESCRIPTION (descripción del problema)
     - SOLUCION (respuesta al usuario, si está disponible)
     - FESOLICITA (fecha de creación, formateada)
     - FESOLUCION (fecha de solución, si aplica, formateada)
     - AI_CLASSIFICATION_DATA (opcional, mostrar información de clasificación si está disponible)
   - Usar `useFetchRequests()` para obtener datos
   - Estados visuales:
     - Badge/indicador de color según estado (Pendiente: amarillo, En Trámite: azul, Solucionado: verde)
     - Mostrar "Sin solución aún" si `SOLUCION` es null
     - Mostrar fecha formateada con `date-fns` (ej: "15 Ene 2024, 10:30")
   - Paginación:
     - Botones "Anterior" / "Siguiente"
     - Mostrar "Mostrando X-Y de Z solicitudes"
   - Responsive:
     - En mobile: mostrar como cards en lugar de tabla
     - En desktop: tabla completa

2. Componente de detalle de solicitud (opcional):
   - Modal o página de detalle que muestra:
     - Todos los campos de la solicitud
     - Historial de cambios (si está disponible)
     - Información completa de `AI_CLASSIFICATION_DATA` formateada

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/features/requests/RequestTable.tsx`
- `agm-simulated-enviroment/frontend/src/components/ui/RequestDetailModal.tsx` (opcional)

### 4.4. Página de Dashboard

**Objetivo**: Crear página principal que combina formulario y tabla de solicitudes.

**Tareas**:
1. Crear `src/pages/Dashboard.tsx`:
   - Layout con dos secciones:
     - Sección superior: `RequestForm` (formulario para crear solicitud)
     - Sección inferior: `RequestTable` (tabla de solicitudes)
   - Header con:
     - Información del usuario (email, botón de logout)
     - Título "Mesa de Servicio"
   - Protegida con `ProtectedRoute`
   - Estilos con Tailwind CSS:
     - Diseño responsive
     - Espaciado adecuado entre secciones
     - Loading states mientras cargan datos

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/pages/Dashboard.tsx`
- `agm-simulated-enviroment/frontend/src/components/layout/Header.tsx` (opcional, para reutilizar header)

---

## FASE 5: Validaciones y Manejo de Errores

**Objetivo**: Estandarizar el manejo de errores y validaciones en todo el frontend para mejorar la experiencia de usuario.

### 5.1. Manejo Centralizado de Errores

**Tareas**:
1. Crear `src/lib/error-handler.ts`:
   - Función `handleApiError(error: unknown): string`:
     - Convierte errores de API a mensajes amigables
     - Maneja errores de Supabase Auth
     - Maneja errores del backend FastAPI
     - Retorna mensaje legible para el usuario
   - Función `isApiError(error: unknown): boolean`:
     - Verifica si un error es de tipo API

2. Crear componente `ErrorBoundary`:
   - Componente que captura errores de React
   - Muestra mensaje amigable al usuario
   - Opción de reportar error o recargar página

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/lib/error-handler.ts`
- `agm-simulated-enviroment/frontend/src/components/ui/ErrorBoundary.tsx`

### 5.2. Validación de Formularios

**Tareas**:
1. Asegurar que todos los formularios usen Zod + react-hook-form:
   - Validación en tiempo real
   - Mensajes de error claros y específicos
   - Prevenir envío si hay errores

2. Validaciones específicas:
   - Email: formato válido
   - Password: mínimo 6 caracteres (o según política)
   - Description: mínimo 1 carácter, máximo 4000
   - Categoría: debe ser válida (300 o 400, o validar contra lista)

**Archivos a modificar**:
- Todos los componentes de formulario
- `src/lib/validation_schemas.ts`

### 5.3. Estados de Carga y Feedback Visual

**Tareas**:
1. Implementar estados de carga consistentes:
   - Spinner o skeleton mientras cargan datos
   - Botones deshabilitados durante envío de formularios
   - Indicadores de progreso cuando sea apropiado

2. Feedback de éxito/error:
   - Toasts o notificaciones para acciones exitosas
   - Mensajes de error visibles y accionables
   - Confirmaciones para acciones destructivas

**Archivos a crear/modificar**:
- `agm-simulated-enviroment/frontend/src/components/ui/Toast.tsx` (opcional)
- `agm-simulated-enviroment/frontend/src/components/ui/LoadingSpinner.tsx` (opcional)

---

## Notas de Implementación

### Sistema de Iconos

**Requisitos**:
- **NO usar emojis** en la interfaz de usuario
- Usar iconos modernos, elegantes y de uso gratuito
- Iconos deben ser consistentes en estilo y tamaño
- Soporte para React/TypeScript

**Biblioteca Recomendada: Lucide React**

**Justificación**: Lucide React es una biblioteca moderna de iconos que cumple con todos los requisitos:
- ✅ **Gratuita y open source**: MIT License
- ✅ **Más de 1000 iconos**: Colección extensa y bien mantenida
- ✅ **Diseño moderno y elegante**: Estilo minimalista y sobrio, perfecto para diseño corporativo
- ✅ **Optimizada para React**: Tree-shakeable, solo importa los iconos usados
- ✅ **TypeScript**: Tipos completos incluidos
- ✅ **Personalizable**: Tamaño, color y stroke-width configurables
- ✅ **Ligera**: Sin dependencias pesadas

**Instalación**:
```bash
npm install lucide-react
```

**Uso**:
```typescript
import { User, Lock, CheckCircle, AlertCircle, Clock } from 'lucide-react'

// En componentes
<User className="w-5 h-5 text-gray-600" />
<CheckCircle className="w-6 h-6 text-green-500" />
```

**Alternativas Consideradas**:
- **Heroicons**: Excelente opción, pero menos iconos que Lucide
- **Phosphor Icons**: Buena alternativa, pero menos popular
- **Material Icons**: Más pesada y menos moderna
- **Font Awesome**: Requiere plan premium para iconos modernos

**Iconos Específicos para el Proyecto**:
- Autenticación: `User`, `Lock`, `LogIn`, `LogOut`
- Estados: `CheckCircle` (Solucionado), `Clock` (En Trámite), `AlertCircle` (Pendiente)
- Acciones: `Plus` (Crear), `Edit`, `Trash2`, `Eye` (Ver detalles)
- Navegación: `Home`, `Menu`, `X` (Cerrar)
- Feedback: `Check`, `X`, `AlertTriangle`, `Info`
- Solicitudes: `FileText`, `MessageSquare`, `Settings`

**Directrices de Uso**:
- Tamaño estándar: `w-5 h-5` (20px) para iconos inline, `w-6 h-6` (24px) para botones
- Color: Usar colores de la paleta corporativa (ver sección "Paleta de Colores Corporativa")
- Stroke width: `strokeWidth={2}` por defecto para mejor legibilidad
- Consistencia: Usar el mismo icono para la misma acción en toda la aplicación

### Diseño Corporativo Elegante y Sobrio

**Principios de Diseño**:

1. **Minimalismo Funcional**:
   - Eliminar elementos innecesarios
   - Priorizar claridad y eficiencia
   - Líneas limpias y espacios en blanco generosos
   - Paleta de colores limitada y coherente

2. **Consistencia Visual**:
   - Mismo estilo de iconos en toda la aplicación
   - Tipografía consistente (ver sección "Tipografía")
   - Espaciado uniforme usando sistema de spacing de Tailwind
   - Componentes reutilizables para mantener coherencia

3. **Jerarquía Visual**:
   - Usar tamaño, color y contraste para destacar información importante
   - Títulos claramente diferenciados de contenido
   - Estados visuales distintivos (hover, active, disabled)

4. **Legibilidad**:
   - Contraste suficiente entre texto y fondo (WCAG AA mínimo)
   - Tamaños de fuente adecuados (mínimo 14px para body)
   - Espaciado entre líneas cómodo (line-height: 1.5-1.6)

### Paleta de Colores Corporativa

**Colores Principales**:
- **Primario**: Azul corporativo (ej: `#2563eb` - blue-600 de Tailwind)
  - Uso: Botones principales, enlaces, elementos interactivos
- **Secundario**: Gris neutro (ej: `#64748b` - slate-500)
  - Uso: Texto secundario, bordes, elementos de soporte
- **Éxito**: Verde (`#10b981` - emerald-500)
  - Uso: Estados exitosos, confirmaciones
- **Advertencia**: Amarillo/Naranja (`#f59e0b` - amber-500)
  - Uso: Estados pendientes, advertencias
- **Error**: Rojo (`#ef4444` - red-500)
  - Uso: Errores, acciones destructivas
- **Info**: Azul claro (`#3b82f6` - blue-500)
  - Uso: Información, estados en trámite

**Colores de Fondo**:
- **Fondo Principal**: Blanco (`#ffffff`) o gris muy claro (`#f8fafc` - slate-50)
- **Fondo Secundario**: Gris claro (`#f1f5f9` - slate-100) para secciones
- **Fondo Hover**: Gris suave (`#e2e8f0` - slate-200) para elementos interactivos

**Colores de Texto**:
- **Texto Principal**: Casi negro (`#0f172a` - slate-900)
- **Texto Secundario**: Gris medio (`#64748b` - slate-500)
- **Texto Deshabilitado**: Gris claro (`#cbd5e1` - slate-300)

**Implementación en Tailwind**:
```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#2563eb',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // ... otros colores corporativos
      }
    }
  }
}
```

### Tipografía

**Fuente Principal**: Sistema de fuentes del sistema (San Francisco en macOS, Segoe UI en Windows, Roboto en Android)
- **Fallback**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`

**Alternativa Recomendada**: Inter o Geist (fuentes modernas y profesionales)
- Si se requiere fuente personalizada, usar Inter de Google Fonts
- Peso: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

**Tamaños de Fuente**:
- **H1**: `text-3xl` (30px) - Títulos principales
- **H2**: `text-2xl` (24px) - Subtítulos
- **H3**: `text-xl` (20px) - Secciones
- **Body**: `text-base` (16px) - Texto principal
- **Small**: `text-sm` (14px) - Texto secundario, labels
- **XS**: `text-xs` (12px) - Notas, metadata

**Line Height**:
- Títulos: `leading-tight` (1.25)
- Body: `leading-normal` (1.5)
- Texto pequeño: `leading-relaxed` (1.625)

### Espaciado y Layout

**Sistema de Espaciado**:
- Usar escala de Tailwind: `4, 8, 12, 16, 24, 32, 48, 64, 96, 128`
- Espaciado consistente entre elementos relacionados
- Padding generoso en componentes interactivos (mínimo `p-4`)

**Grid y Layout**:
- Usar CSS Grid para layouts complejos
- Flexbox para alineación y distribución
- Máximo ancho de contenido: `max-w-7xl` (1280px) centrado
- Padding lateral: `px-4 sm:px-6 lg:px-8`

**Componentes de Layout**:
- **Container**: Ancho máximo centrado con padding responsive
- **Card**: Fondo blanco, sombra sutil (`shadow-sm`), border radius (`rounded-lg`)
- **Section**: Espaciado vertical consistente (`py-8` o `py-12`)

### Componentes UI Base

**Botones**:
- Estilo: Bordes redondeados (`rounded-md`), padding adecuado (`px-4 py-2`)
- Estados: Hover, active, disabled claramente diferenciados
- Variantes: Primary (azul), Secondary (gris), Danger (rojo), Ghost (sin fondo)
- Tamaños: Small (`text-sm py-1.5 px-3`), Medium (default), Large (`text-lg py-3 px-6`)

**Inputs y Formularios**:
- Borde sutil (`border border-gray-300`)
- Focus: Borde azul (`focus:border-blue-500 focus:ring-2 focus:ring-blue-200`)
- Estados de error: Borde rojo y mensaje de error visible
- Placeholder: Color gris claro (`placeholder-gray-400`)

**Badges y Estados**:
- Estados de solicitud: Badges con colores semánticos
  - Pendiente: Fondo amarillo claro, texto amarillo oscuro
  - En Trámite: Fondo azul claro, texto azul oscuro
  - Solucionado: Fondo verde claro, texto verde oscuro
- Tamaño: `px-2.5 py-0.5 text-xs font-medium rounded-full`

**Tablas**:
- Filas alternadas: Fondo gris muy claro en filas pares
- Hover: Fondo gris claro en fila hover
- Bordes: Líneas sutiles entre filas (`border-b border-gray-200`)
- Padding: `px-6 py-4` en celdas

### Accesibilidad

**Requisitos WCAG AA**:
- Contraste mínimo 4.5:1 para texto normal
- Contraste mínimo 3:1 para texto grande (18px+)
- Focus visible en todos los elementos interactivos
- Labels asociados a todos los inputs
- ARIA labels cuando sea necesario

**Navegación por Teclado**:
- Todos los elementos interactivos deben ser accesibles por teclado
- Orden de tabulación lógico
- Skip links para navegación rápida

**Indicadores Visuales**:
- No depender solo del color para transmitir información
- Usar iconos y texto junto con colores
- Estados de focus claramente visibles

### Responsive Design

**Breakpoints de Tailwind**:
- `sm`: 640px - Tablets pequeñas
- `md`: 768px - Tablets
- `lg`: 1024px - Laptops
- `xl`: 1280px - Desktops
- `2xl`: 1536px - Pantallas grandes

**Estrategia Mobile-First**:
- Diseñar primero para mobile
- Agregar mejoras progresivas para pantallas más grandes
- Tablas: Convertir a cards en mobile (ver "Componente de Tabla de Solicitudes")
- Navegación: Menú hamburguesa en mobile, menú horizontal en desktop
- Formularios: Campos apilados en mobile, layout horizontal en desktop cuando sea apropiado

**Componentes Responsive**:
- **RequestTable**: Cards en mobile (`< md`), tabla completa en desktop (`>= md`)
- **Dashboard**: Layout vertical en mobile, dos columnas en desktop
- **Header**: Menú colapsable en mobile, menú expandido en desktop

### Mapeo de USUSOLICITA

**Decisión**: `USUSOLICITA` se extrae del email del usuario autenticado en el backend, pero el frontend debe validar que el username no exceda 25 caracteres antes de permitir el registro.

**Estrategia**:
- El frontend puede mostrar una advertencia si el email del usuario resultaría en un username > 25 caracteres
- La validación crítica se hace en el backend
- Helper `extractUsernameFromEmail()` en `api_services/auth.ts` para uso interno

### Integración con Backend

**Endpoints del Backend**:
- `POST /api/requests`: Crear solicitud (requiere JWT)
- `GET /api/requests`: Listar solicitudes (requiere JWT, paginación)
- `GET /api/requests/{id}`: Obtener solicitud específica (requiere JWT)
- `PATCH /api/requests/{id}`: Actualizar solicitud (requiere JWT, limitado)

**Autenticación**:
- Obtener token JWT de Supabase: `supabase.auth.getSession()`
- Incluir en headers: `Authorization: Bearer <token>`
- Manejar errores 401 (token expirado): redirigir a login

### Supabase Realtime

**Configuración**:
- Realtime debe estar habilitado en Supabase Dashboard para la tabla `HLP_PETICIONES`
- Eventos: INSERT, UPDATE (DELETE opcional)
- Filtro por `USUSOLICITA` para mostrar solo solicitudes del usuario

**Implementación**:
```typescript
const channel = supabase
  .channel('requests-changes')
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'HLP_PETICIONES',
    filter: `USUSOLICITA=eq.${username}`
  }, (payload) => {
    // Actualizar estado
  })
  .subscribe()
```

**Limpieza**:
- Siempre limpiar suscripción en cleanup de `useEffect`
- Desuscribirse cuando el componente se desmonta o el usuario cierra sesión

### Conversión de Estados

**Mapeo CODESTADO → Texto**:
- `1` → "Pendiente"
- `2` → "En Trámite"
- `3` → "Solucionado"

**Implementación**:
```typescript
const ESTADO_MAP: Record<number, string> = {
  1: 'Pendiente',
  2: 'En Trámite',
  3: 'Solucionado'
}

function getEstadoText(codestado: number | null): string {
  return ESTADO_MAP[codestado ?? 1] || 'Desconocido'
}
```

### Estilos con Tailwind CSS

**Enfoque**:
- Utility-first: usar clases de Tailwind directamente
- Componentes reutilizables en `components/ui/` para elementos comunes
- Responsive design: mobile-first (ver sección "Responsive Design")
- Dark mode: opcional, configurar si se requiere

**Integración con Sistema de Diseño**:
- **Paleta de Colores**: Usar colores definidos en la sección "Paleta de Colores Corporativa"
- **Tipografía**: Aplicar tamaños y line-heights definidos en la sección "Tipografía"
- **Espaciado**: Seguir sistema de spacing definido en la sección "Espaciado y Layout"
- **Iconos**: Usar Lucide React según directrices en la sección "Sistema de Iconos"

**Componentes UI Base**:
- **Button**: Ver especificaciones en "Componentes UI Base" (variantes, tamaños, estados)
- **Input, Textarea, Select**: Ver especificaciones en "Componentes UI Base" (bordes, focus, errores)
- **Badge**: Ver especificaciones en "Componentes UI Base" (estados de solicitud)
- **Card**: Ver especificaciones en "Componentes de Layout"
- **Modal, Toast, LoadingSpinner**: Componentes de feedback visual
- **Table**: Ver especificaciones en "Componentes UI Base" (filas alternadas, hover, bordes)

**Configuración de Tailwind**:
- Extender colores corporativos en `tailwind.config.js` (ver ejemplo en "Paleta de Colores Corporativa")
- Configurar fuentes del sistema (ver "Tipografía")
- Asegurar contraste WCAG AA (ver "Accesibilidad")

### Service Layer Pattern

**Importancia**: La capa `api_services/` es crucial para facilitar la migración a producción.

**Estructura**:
- `supabase_client.ts`: Cliente de Supabase
- `auth.ts`: Funciones de autenticación
- `requests.ts`: Funciones CRUD de solicitudes

**Ventajas**:
- Abstracción de la implementación (Supabase SDK vs llamadas directas al backend)
- Fácil migración cuando se cambien las APIs
- Testing más sencillo (mock de servicios)

### Manejo de Tokens JWT

**Almacenamiento**:
- Supabase SDK maneja automáticamente el almacenamiento del token
- No almacenar tokens manualmente en localStorage (riesgo de XSS)
- Usar `supabase.auth.getSession()` para obtener token cuando sea necesario

**Renovación**:
- Supabase SDK renueva tokens automáticamente
- Manejar errores 401: token expirado, redirigir a login

### Formateo de Fechas

**Biblioteca**: `date-fns`

**Ejemplo**:
```typescript
import { format } from 'date-fns'
import { es } from 'date-fns/locale' // Opcional: español

const formattedDate = format(new Date(fesolicita), 'dd MMM yyyy, HH:mm', { locale: es })
// Resultado: "15 Ene 2024, 10:30"
```

### AI_CLASSIFICATION_DATA

**Estructura**:
```typescript
interface AIClassificationData {
  app_type: 'amerika' | 'dominio'
  confidence: number // 0.0 - 1.0
  classification_timestamp: string // ISO8601
  detected_actions: string[]
  raw_classification?: string
}
```

**Visualización**:
- Mostrar en tabla como badge o tooltip
- Página de detalle: mostrar información completa formateada
- Opcional: mostrar confianza como barra de progreso

---

## Orden de Implementación Recomendado

1. **Fase 1** (Configuración): Establece base del proyecto
2. **Fase 2** (Autenticación): Necesaria para todas las funcionalidades
3. **Fase 3** (Formulario): Permite crear solicitudes
4. **Fase 4** (Visualización + Realtime): Muestra solicitudes y actualizaciones en tiempo real
5. **Fase 5** (Validaciones y Errores): Mejora robustez y UX

---

## Referencias Cruzadas

- [Plan de Desarrollo Principal](./02_dev_plan.md) - Paso 3 (versión resumida)
- [Especificación del Backend](./03_backend_detailed.md) - Endpoints y estructura de datos
- [Guía de Setup](./01_setup.md) - Configuración inicial del proyecto
- [Mapeo de Nomenclatura](../docs/NAMING_MAPPING.md) - Convenciones de nombres
- [Estructura del Frontend](../docs/README.md#estructura-del-frontend-agm-simulated-enviromentfrontend) - Organización de archivos

