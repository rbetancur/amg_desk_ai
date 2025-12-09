import { useState, useEffect, useCallback } from 'react'
import { getRequests } from '../api_services/requests'
import { supabase } from '../api_services/supabase_client'
import type { Request } from '../lib/types'
import { useSupabaseAuth } from './useSupabaseAuth'

interface UseFetchRequestsReturn {
  requests: Request[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  pagination: {
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
}

export function useFetchRequests(
  limit: number = 50,
  offset: number = 0
): UseFetchRequestsReturn {
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [pagination, setPagination] = useState({
    total: 0,
    limit,
    offset,
    has_more: false,
  })
  const { username, isAuthenticated } = useSupabaseAuth()

  const fetchRequests = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await getRequests(limit, offset)
      // Normalizar la respuesta: siempre debe tener items (array) y pagination
      setRequests(Array.isArray(response.items) ? response.items : [])
      setPagination({
        total: response.pagination?.total ?? 0,
        limit: response.pagination?.limit ?? limit,
        offset: response.pagination?.offset ?? offset,
        has_more: response.pagination?.has_more ?? false,
      })
    } catch (err) {
      console.error('Error al obtener solicitudes:', err)
      const errorMessage = err instanceof Error ? err.message : 'Error al obtener solicitudes'
      setError(new Error(errorMessage))
    } finally {
      setLoading(false)
    }
  }, [limit, offset, isAuthenticated])

  // Cargar solicitudes iniciales
  useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  // Suscripción a Realtime
  useEffect(() => {
    if (!isAuthenticated || !username) {
      return
    }

    const channel = supabase
      .channel('requests-changes')
      .on(
        'postgres_changes',
        {
          event: '*', // INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'HLP_PETICIONES',
          filter: `USUSOLICITA=eq.${username}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            // Agregar nueva solicitud
            setRequests((prev) => [payload.new as Request, ...prev])
            setPagination((prev) => ({ ...prev, total: prev.total + 1 }))
          } else if (payload.eventType === 'UPDATE') {
            // Actualizar solicitud existente
            setRequests((prev) =>
              prev.map((req) =>
                req.codpeticiones === (payload.new as Request).codpeticiones
                  ? (payload.new as Request)
                  : req
              )
            )
          } else if (payload.eventType === 'DELETE') {
            // Remover solicitud
            setRequests((prev) =>
              prev.filter((req) => req.codpeticiones !== (payload.old as Request).codpeticiones)
            )
            setPagination((prev) => ({ ...prev, total: Math.max(0, prev.total - 1) }))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [isAuthenticated, username])

  return {
    requests,
    loading,
    error,
    refetch: fetchRequests,
    pagination,
  }
}

