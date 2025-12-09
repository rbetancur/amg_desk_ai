-- ============================================
-- Script de Prueba: Validar RLS con Username
-- ============================================
-- Este script ayuda a validar que la función y las políticas RLS
-- funcionan correctamente con username extraído del email.
--
-- IMPORTANTE: 
-- - Ejecuta este script DESPUÉS de ejecutar setup-rls-username.sql
-- - Algunas pruebas requieren estar autenticado como usuario
-- - Otras pruebas requieren usar SUPABASE_SERVICE_ROLE_KEY
-- ============================================

-- ============================================
-- Prueba 1: Verificar que la función existe
-- ============================================

SELECT 
  routine_name,
  routine_type,
  data_type as return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'get_username_from_auth_user';

-- Debe retornar 1 fila con la función

-- ============================================
-- Prueba 2: Verificar estructura de la función
-- ============================================

SELECT 
  p.proname as function_name,
  pg_get_functiondef(p.oid) as function_definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname = 'get_username_from_auth_user';

-- Debe mostrar la definición completa de la función

-- ============================================
-- Prueba 3: Verificar que las políticas existen
-- ============================================

SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd as operation,
  CASE 
    WHEN qual IS NOT NULL THEN 'USING clause presente'
    ELSE 'Sin USING clause'
  END as using_clause,
  CASE 
    WHEN with_check IS NOT NULL THEN 'WITH CHECK clause presente'
    ELSE 'Sin WITH CHECK clause'
  END as with_check_clause
FROM pg_policies
WHERE tablename = 'HLP_PETICIONES'
ORDER BY 
  CASE cmd
    WHEN 'SELECT' THEN 1
    WHEN 'INSERT' THEN 2
    WHEN 'UPDATE' THEN 3
    ELSE 4
  END,
  policyname;

-- Debe retornar 3 políticas (SELECT, INSERT, UPDATE)

-- ============================================
-- Prueba 4: Verificar contenido de las políticas
-- ============================================
-- Verifica que las políticas usen get_username_from_auth_user()
-- ============================================

SELECT 
  policyname,
  cmd as operation,
  qual as policy_condition
FROM pg_policies
WHERE tablename = 'HLP_PETICIONES'
  AND qual NOT LIKE '%get_username_from_auth_user%';

-- Debe retornar 0 filas (todas las políticas deben usar la función)

-- ============================================
-- Prueba 5: Verificar RLS está habilitado
-- ============================================

SELECT 
  schemaname,
  tablename,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'HLP_PETICIONES';

-- rowsecurity debe ser 'true'

-- ============================================
-- Prueba 6: Probar función con usuario autenticado
-- ============================================
-- NOTA: Esta prueba debe ejecutarse como usuario autenticado
-- desde el frontend o usando el cliente de Supabase con JWT
-- ============================================

-- Ejecutar desde el frontend o cliente de Supabase:
-- SELECT get_username_from_auth_user();
--
-- Debe retornar el username (parte antes de @) del email del usuario autenticado
-- Ejemplo: Si el email es mzuloaga@aguasdemanizales.com.co, debe retornar 'mzuloaga'

-- ============================================
-- Prueba 7: Verificar que Service Role Key bypass RLS
-- ============================================
-- NOTA: Esta prueba debe ejecutarse usando SUPABASE_SERVICE_ROLE_KEY
-- desde el backend o Agente AI
-- ============================================

-- Ejecutar desde el backend usando SUPABASE_SERVICE_ROLE_KEY:
-- SELECT COUNT(*) FROM "HLP_PETICIONES";
--
-- Debe retornar el conteo total de solicitudes sin restricciones RLS

-- ============================================
-- Prueba 8: Validar edge cases (desde backend)
-- ============================================
-- Estas pruebas deben ejecutarse desde el backend con diferentes usuarios
-- ============================================

-- Caso 1: Usuario con email normal
-- Email: mzuloaga@aguasdemanizales.com.co
-- Esperado: get_username_from_auth_user() = 'mzuloaga'

-- Caso 2: Usuario con email Gmail (PoC)
-- Email: mzuloaga@gmail.com
-- Esperado: get_username_from_auth_user() = 'mzuloaga'

-- Caso 3: Usuario con username largo
-- Email: usuario.muy.largo@aguasdemanizales.com.co
-- Esperado: get_username_from_auth_user() = 'usuario.muy.largo'
-- NOTA: El backend debe validar que no exceda 25 caracteres

-- Caso 4: Usuario con caracteres especiales en username
-- Email: usuario_123@aguasdemanizales.com.co
-- Esperado: get_username_from_auth_user() = 'usuario_123'

-- ============================================
-- Prueba 9: Validar políticas RLS (desde frontend/backend)
-- ============================================
-- Estas pruebas requieren ejecutarse con usuarios autenticados
-- ============================================

-- Prueba 9.1: Usuario solo ve sus propias solicitudes
-- 1. Autenticarse como usuario A (ej: mzuloaga@aguasdemanizales.com.co)
-- 2. Crear una solicitud (debe tener USUSOLICITA = 'mzuloaga')
-- 3. Listar solicitudes (debe ver solo sus propias solicitudes)
--
-- SQL desde frontend con JWT de usuario A:
-- SELECT * FROM "HLP_PETICIONES";
-- Debe retornar solo solicitudes donde USUSOLICITA = 'mzuloaga'

-- Prueba 9.2: Usuario no puede ver solicitudes de otros
-- 1. Autenticarse como usuario B (ej: otro@aguasdemanizales.com.co)
-- 2. Intentar ver solicitudes del usuario A
--
-- SQL desde frontend con JWT de usuario B:
-- SELECT * FROM "HLP_PETICIONES" WHERE "USUSOLICITA" = 'mzuloaga';
-- Debe retornar 0 filas (RLS bloquea el acceso)

-- Prueba 9.3: Usuario solo puede crear solicitudes con su propio username
-- 1. Autenticarse como usuario A
-- 2. Intentar crear solicitud con USUSOLICITA diferente
--
-- SQL desde frontend con JWT de usuario A:
-- INSERT INTO "HLP_PETICIONES" ("CODCATEGORIA", "USUSOLICITA", "DESCRIPTION")
-- VALUES (300, 'otro_usuario', 'Test');
-- Debe fallar (RLS bloquea el INSERT)

-- ============================================
-- Resumen de Validación
-- ============================================
-- 
-- ✅ Prueba 1: Función existe
-- ✅ Prueba 2: Función tiene estructura correcta
-- ✅ Prueba 3: Políticas existen (SELECT, INSERT, UPDATE)
-- ✅ Prueba 4: Políticas usan get_username_from_auth_user()
-- ✅ Prueba 5: RLS está habilitado
-- ⚠️ Prueba 6: Requiere usuario autenticado (probar desde frontend)
-- ⚠️ Prueba 7: Requiere SERVICE_ROLE_KEY (probar desde backend)
-- ⚠️ Prueba 8: Requiere múltiples usuarios (probar desde backend)
-- ⚠️ Prueba 9: Requiere usuarios autenticados (probar desde frontend/backend)
--
-- Las pruebas marcadas con ⚠️ requieren ejecutarse con autenticación real
-- y deben realizarse durante el desarrollo del frontend y backend.
-- ============================================

