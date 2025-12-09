import { getBackendUrl } from '../lib/constants'
import type { Request, RequestCreate, PaginatedResponse } from '../lib/types'
import { supabase } from './supabase_client'

/**
 * Obtiene los headers de autenticación con el token JWT
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session?.access_token) {
    throw new Error('No hay sesión activa. Por favor, inicia sesión.')
  }

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${session.access_token}`,
  }
}

/**
 * Crea una nueva solicitud
 */
export async function createRequest(data: RequestCreate): Promise<Request> {
  const headers = await getAuthHeaders()
  const response = await fetch(getBackendUrl('/api/requests'), {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Error al crear solicitud' }))
    throw new Error(error.message || 'Error al crear solicitud')
  }

  return response.json()
}

/**
 * Obtiene las solicitudes del usuario con paginación
 */
export async function getRequests(
  limit: number = 50,
  offset: number = 0
): Promise<PaginatedResponse<Request>> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(
      getBackendUrl(`/api/requests?limit=${limit}&offset=${offset}`),
      {
        method: 'GET',
        headers,
      }
    )

    if (!response.ok) {
      let errorMessage = 'Error al obtener solicitudes'
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Si no se puede parsear el JSON, usar el mensaje por defecto
        if (response.status === 401) {
          errorMessage = 'No autorizado. Por favor, inicia sesión nuevamente.'
        } else if (response.status === 500) {
          errorMessage = 'Error del servidor. Por favor, intenta más tarde.'
        } else if (response.status >= 400) {
          errorMessage = `Error ${response.status}: ${response.statusText}`
        }
      }
      throw new Error(errorMessage)
    }

    try {
      const data = await response.json()
      // Asegurar que siempre tenemos una estructura válida
      return {
        items: data.items || [],
        pagination: data.pagination || {
          total: 0,
          limit,
          offset,
          has_more: false,
        },
      }
    } catch (err) {
      console.error('Error al parsear respuesta:', err)
      throw new Error('Error al procesar la respuesta del servidor')
    }
  } catch (err) {
    // Capturar errores de red (Connection refused, timeout, etc.)
    if (err instanceof TypeError && err.message.includes('fetch')) {
      const backendUrl = getBackendUrl('/api/requests')
      throw new Error(
        `No se pudo conectar al backend (${backendUrl}). Verifica que el servidor esté corriendo en ${backendUrl.replace('/api/requests', '')}`
      )
    }
    // Re-lanzar otros errores
    throw err
  }
}

/**
 * Obtiene una solicitud por ID
 */
export async function getRequestById(id: number): Promise<Request> {
  const headers = await getAuthHeaders()
  const response = await fetch(getBackendUrl(`/api/requests/${id}`), {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Solicitud no encontrada')
    }
    const error = await response.json().catch(() => ({ message: 'Error al obtener solicitud' }))
    throw new Error(error.message || 'Error al obtener solicitud')
  }

  return response.json()
}

