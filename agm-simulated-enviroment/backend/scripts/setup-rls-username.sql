-- ============================================
-- Script: Configurar RLS para USUSOLICITA (Username extraído del email)
-- ============================================
-- Este script crea la función helper y las políticas RLS necesarias
-- para que los usuarios solo puedan acceder a sus propias solicitudes
-- basándose en el username extraído de su email.
--
-- IMPORTANTE: 
-- - Ejecuta este script DESPUÉS de crear las tablas con las migraciones
-- - Asegúrate de que RLS esté habilitado en la tabla HLP_PETICIONES
-- - Este script asume que USUSOLICITA contiene el username (parte antes de @)
--   extraído del email del usuario autenticado
-- ============================================

-- ============================================
-- Paso 1: Crear función helper para extraer username del email
-- ============================================
-- Esta función extrae la parte antes de @ del email del usuario autenticado
-- Ejemplo: mzuloaga@aguasdemanizales.com.co -> mzuloaga
-- ============================================

CREATE OR REPLACE FUNCTION get_username_from_auth_user()
RETURNS TEXT AS $$
  SELECT SUBSTRING(
    (SELECT email FROM auth.users WHERE id = auth.uid()) 
    FROM '^([^@]+)'
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Comentario sobre la función
COMMENT ON FUNCTION get_username_from_auth_user() IS 
'Extrae el username (parte antes de @) del email del usuario autenticado. Usado en políticas RLS para comparar con USUSOLICITA.';

-- ============================================
-- Paso 2: Eliminar políticas antiguas si existen
-- ============================================
-- Descomenta las siguientes líneas si necesitas eliminar políticas antiguas
-- que usan auth.uid()::text = USUSOLICITA
-- ============================================

-- DROP POLICY IF EXISTS "Users can view own requests" ON "HLP_PETICIONES";
-- DROP POLICY IF EXISTS "Users can create requests" ON "HLP_PETICIONES";
-- DROP POLICY IF EXISTS "Users can update own requests" ON "HLP_PETICIONES";

-- ============================================
-- Paso 3: Crear política para SELECT (ver solicitudes)
-- ============================================
-- Los usuarios solo pueden ver solicitudes donde USUSOLICITA coincide
-- con su username extraído del email
-- ============================================

CREATE POLICY "Users can view own requests"
ON "HLP_PETICIONES"
FOR SELECT
USING (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- ============================================
-- Paso 4: Crear política para INSERT (crear solicitudes)
-- ============================================
-- Los usuarios solo pueden crear solicitudes donde USUSOLICITA coincide
-- con su username extraído del email
-- ============================================

CREATE POLICY "Users can create requests"
ON "HLP_PETICIONES"
FOR INSERT
WITH CHECK (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- ============================================
-- Paso 5: Crear política para UPDATE (actualizar solicitudes)
-- ============================================
-- Los usuarios solo pueden actualizar solicitudes donde USUSOLICITA coincide
-- con su username extraído del email
-- ============================================

CREATE POLICY "Users can update own requests"
ON "HLP_PETICIONES"
FOR UPDATE
USING (
  get_username_from_auth_user() = "USUSOLICITA"
)
WITH CHECK (
  get_username_from_auth_user() = "USUSOLICITA"
);

-- ============================================
-- Paso 6: Verificar que todo se creó correctamente
-- ============================================
-- Esta consulta muestra todas las políticas creadas para HLP_PETICIONES
-- ============================================

SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual
FROM pg_policies
WHERE tablename = 'HLP_PETICIONES'
ORDER BY policyname;

-- ============================================
-- Notas importantes:
-- ============================================
-- 1. La función get_username_from_auth_user() usa SECURITY DEFINER para
--    acceder a auth.users, lo cual es necesario para políticas RLS.
--
-- 2. Las políticas RLS consultan auth.users en cada operación. Este overhead
--    es aceptable para la PoC, pero puede optimizarse en producción usando
--    metadata del usuario almacenada en user_metadata.
--
-- 3. El backend debe validar que el username no exceda 25 caracteres
--    (límite de VARCHAR(25) en USUSOLICITA) antes de insertar.
--
-- 4. El SUPABASE_SERVICE_ROLE_KEY permite bypass automático de RLS.
--    El Agente AI usará esta clave para leer y actualizar todas las solicitudes.
--
-- 5. Si dos usuarios tienen el mismo username pero diferentes dominios
--    (ej: mzuloaga@aguasdemanizales.com.co y mzuloaga@gmail.com),
--    ambos tendrán el mismo USUSOLICITA. Esto es aceptable para la PoC,
--    pero debe considerarse para producción.
-- ============================================

