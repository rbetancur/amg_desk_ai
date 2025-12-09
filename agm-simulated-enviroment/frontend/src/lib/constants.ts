// URL base del backend
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

/**
 * Obtiene la URL completa del endpoint del backend
 */
export function getBackendUrl(endpoint: string): string {
  const baseUrl = BACKEND_URL.replace(/\/$/, '') // Remover trailing slash
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${path}`
}

// Categorías disponibles
export const CATEGORIES = [
  { codcategoria: 300, categoria: 'Cambio de Contraseña Cuenta Dominio' },
  { codcategoria: 400, categoria: 'Cambio de Contraseña Amerika' },
] as const

// Mapeo de estados
export const ESTADO_MAP: Record<number, string> = {
  1: 'Pendiente',
  2: 'En Trámite',
  3: 'Solucionado',
}

/**
 * Convierte CODESTADO numérico a texto legible
 */
export function getEstadoText(codestado: number | null): string {
  return ESTADO_MAP[codestado ?? 1] || 'Desconocido'
}

