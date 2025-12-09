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

/**
 * Obtiene el nombre de la categoría desde su código
 */
export function getCategoryName(codcategoria: number): string {
  const category = CATEGORIES.find((cat) => cat.codcategoria === codcategoria)
  return category?.categoria || `Categoría ${codcategoria}`
}

// Mapeo de prioridades
export const PRIORIDAD_MAP: Record<number, string> = {
  1: 'Baja',
  2: 'Media',
  3: 'Alta',
}

/**
 * Convierte CODPRIORIDAD numérico a texto legible
 */
export function getPrioridadText(codprioridad: number | null): string {
  if (codprioridad === null) return 'N/A'
  return PRIORIDAD_MAP[codprioridad] || `Prioridad ${codprioridad}`
}

// Mapeo de gravedades
export const GRAVEDAD_MAP: Record<number, string> = {
  1: 'Baja',
  2: 'Normal',
  3: 'Alta',
}

/**
 * Convierte CODGRAVEDAD numérico a texto legible
 */
export function getGravedadText(codgravedad: number | null): string {
  if (codgravedad === null) return 'N/A'
  return GRAVEDAD_MAP[codgravedad] || `Gravedad ${codgravedad}`
}

// Mapeo de frecuencias
export const FRECUENCIA_MAP: Record<number, string> = {
  1: 'Poco Frecuente',
  2: 'Frecuente',
  3: 'Muy Frecuente',
}

/**
 * Convierte CODFRECUENCIA numérico a texto legible
 */
export function getFrecuenciaText(codfrecuencia: number | null): string {
  if (codfrecuencia === null) return 'N/A'
  return FRECUENCIA_MAP[codfrecuencia] || `Frecuencia ${codfrecuencia}`
}

