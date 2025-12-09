# Frontend - Mesa de Servicio AGM Desk AI

Frontend React para la Mesa de Servicio, desarrollado con TypeScript, Vite, Tailwind CSS y Supabase.

## Requisitos Previos

- Node.js 18+ y npm (o yarn/pnpm)
- Cuenta de Supabase configurada
- Backend FastAPI corriendo (ver [../backend/README.md](../backend/README.md))

## Instalación

1. Instalar dependencias:

```bash
npm install
```

2. Configurar variables de entorno:

Crear archivo `.env.local` en la raíz del proyecto:

```env
VITE_SUPABASE_URL=https://[PROJECT-REF].supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_BACKEND_URL=http://localhost:8000
```

**Cómo obtener las credenciales**:
- Ve a [Supabase Dashboard](https://app.supabase.com/) > Tu Proyecto > Settings > API
- Copia el **Project URL** y el **anon public key**
- Reemplaza `[PROJECT-REF]` con el ID de tu proyecto

**Nota**: El archivo `.env.local` NO debe commitearse (ya está en `.gitignore`)

## Desarrollo

Ejecutar el servidor de desarrollo:

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

## Build para Producción

```bash
npm run build
```

Los archivos compilados estarán en la carpeta `dist/`.

## Estructura del Proyecto

```
src/
├── api_services/     # Servicios de API (Supabase, Backend)
├── assets/           # Recursos estáticos (imágenes, estilos)
├── components/       # Componentes reutilizables
│   ├── layout/       # Componentes de layout
│   └── ui/           # Componentes UI base
├── contexts/         # Contextos React (Auth)
├── features/         # Módulos de funcionalidad
│   ├── auth/         # Autenticación
│   └── requests/     # Solicitudes
├── hooks/            # Custom hooks
├── lib/              # Utilidades y constantes
└── pages/            # Páginas de la aplicación
```

## Tecnologías

- **React 18** - Biblioteca UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server
- **Tailwind CSS** - Framework de estilos
- **React Router** - Routing
- **Supabase** - Autenticación y Realtime
- **Zod** - Validación de esquemas
- **React Hook Form** - Gestión de formularios
- **Lucide React** - Iconos
- **date-fns** - Formateo de fechas

## Características

- ✅ Autenticación con Supabase (Login/Registro)
- ✅ Creación de solicitudes de mesa de servicio
- ✅ Visualización de solicitudes en tiempo real (Supabase Realtime)
- ✅ Diseño responsive (mobile-first)
- ✅ Validación de formularios con Zod
- ✅ Manejo de errores centralizado
- ✅ Diseño corporativo elegante y sobrio

## Notas

- El frontend se comunica con el backend FastAPI para operaciones CRUD
- La autenticación se maneja completamente con Supabase
- Las actualizaciones en tiempo real se reciben vía Supabase Realtime
- El diseño sigue las especificaciones corporativas definidas en `specs/04_frontend_detailed.md`

