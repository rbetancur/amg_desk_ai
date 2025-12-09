# Guía de Instalación - Frontend

## Pasos para Configurar el Proyecto

### 1. Instalar Dependencias

```bash
cd agm-simulated-enviroment/frontend
npm install
```

### 2. Configurar Variables de Entorno

Crear archivo `.env.local` en la raíz del proyecto `agm-simulated-enviroment/frontend/`:

```env
VITE_SUPABASE_URL=https://[PROJECT-REF].supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_BACKEND_URL=http://localhost:8000
```

**Cómo obtener las credenciales de Supabase**:

1. Accede a tu [Supabase Dashboard](https://app.supabase.com/)
2. Selecciona tu proyecto (o crea uno nuevo si no tienes)
3. Ve a **Project Settings** > **API**
4. Copia los siguientes valores:
   - **Project URL**: Este es tu `VITE_SUPABASE_URL`
   - **anon public key**: Este es tu `VITE_SUPABASE_ANON_KEY`

**Importante**: 
- Reemplazar `[PROJECT-REF]` con el ID de tu proyecto de Supabase (se encuentra en la URL del proyecto)
- El archivo `.env.local` NO debe commitearse (ya está en `.gitignore`)
- Reiniciar el servidor de desarrollo después de crear/modificar `.env.local`

### 3. Verificar Backend

Asegurarse de que el backend FastAPI esté corriendo en `http://localhost:8000` (o actualizar `VITE_BACKEND_URL` según corresponda).

### 4. Ejecutar en Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

### 5. Build para Producción

```bash
npm run build
```

Los archivos compilados estarán en `dist/`

## Solución de Problemas

### Error: "Missing Supabase environment variables"

- Verificar que el archivo `.env.local` existe
- Verificar que las variables `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` están configuradas
- Reiniciar el servidor de desarrollo después de crear/modificar `.env.local`

### Error: "Cannot find module"

- Ejecutar `npm install` para instalar todas las dependencias
- Verificar que `node_modules/` existe

### Error de conexión al backend

- Verificar que el backend FastAPI está corriendo
- Verificar que `VITE_BACKEND_URL` apunta a la URL correcta
- Verificar CORS en el backend (debe permitir `http://localhost:3000`)

## Estructura del Proyecto

Ver [README.md](./README.md) para más detalles sobre la estructura y arquitectura del proyecto.

