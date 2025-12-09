import { useState } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale/es'
import { Clock, CheckCircle, AlertCircle, ChevronLeft, ChevronRight, Brain } from 'lucide-react'
import { useFetchRequests } from '../../hooks/useFetchRequests'
import { getEstadoText } from '../../lib/constants'
import type { Request, AIClassificationData } from '../../lib/types'

function EstadoBadge({ codestado }: { codestado: number | null }) {
  const estado = codestado ?? 1
  const estadoText = getEstadoText(estado)

  const styles = {
    1: 'bg-amber-100 text-amber-800 border-amber-200',
    2: 'bg-blue-100 text-blue-800 border-blue-200',
    3: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  }

  const icons = {
    1: AlertCircle,
    2: Clock,
    3: CheckCircle,
  }

  const Icon = icons[estado as keyof typeof icons] || AlertCircle

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full border ${styles[estado as keyof typeof styles]}`}
    >
      <Icon className="w-3 h-3" />
      {estadoText}
    </span>
  )
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  try {
    return format(new Date(dateString), 'dd MMM yyyy, HH:mm', { locale: es })
  } catch {
    return dateString
  }
}

function AIClassificationBadge({ data }: { data: AIClassificationData }) {
  const appTypeColors = {
    amerika: 'bg-purple-100 text-purple-800 border-purple-200',
    dominio: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  }

  const confidencePercent = Math.round(data.confidence * 100)

  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full border ${appTypeColors[data.app_type]}`}
      >
        <Brain className="w-3 h-3" />
        {data.app_type === 'amerika' ? 'Amerika' : 'Dominio'}
      </span>
      <span className="text-xs text-slate-600">
        {confidencePercent}% confianza
      </span>
    </div>
  )
}

export function RequestTable() {
  const [currentOffset, setCurrentOffset] = useState(0)
  const limit = 50
  const { requests, loading, error, pagination } = useFetchRequests(limit, currentOffset)

  const handlePrevious = () => {
    if (currentOffset > 0) {
      setCurrentOffset((prev) => Math.max(0, prev - limit))
    }
  }

  const handleNext = () => {
    if (pagination.has_more) {
      setCurrentOffset((prev) => prev + limit)
    }
  }

  // Calcular rango de solicitudes mostradas
  const startRange = currentOffset + 1
  const endRange = Math.min(currentOffset + requests.length, pagination.total)

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <div className="text-center text-slate-600">Cargando solicitudes...</div>
      </div>
    )
  }

  if (error) {
    // Si el error es de autenticación, mostrar un mensaje más específico
    const isAuthError = error.message.toLowerCase().includes('autorizado') || 
                       error.message.toLowerCase().includes('sesión') ||
                       error.message.toLowerCase().includes('401')
    
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <div className="text-center text-red-600">
          <AlertCircle className="w-6 h-6 mx-auto mb-2" />
          <p className="font-medium mb-1">Error al cargar solicitudes</p>
          <p className="text-sm">{error.message}</p>
          {isAuthError && (
            <p className="text-xs text-slate-500 mt-2">
              Por favor, cierra sesión e inicia sesión nuevamente.
            </p>
          )}
        </div>
      </div>
    )
  }

  if (requests.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <div className="text-center text-slate-600">
          <p>No hay solicitudes registradas</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200">
        <h2 className="text-xl font-semibold text-slate-900">Mis Solicitudes</h2>
        <p className="text-sm text-slate-600 mt-1">
          {pagination.total > 0
            ? `Mostrando ${startRange}-${endRange} de ${pagination.total} solicitudes`
            : 'No hay solicitudes'}
        </p>
      </div>

      {/* Vista Desktop: Tabla */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Descripción
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Solución
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Fecha Creación
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Fecha Solución
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                Clasificación IA
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {requests.map((request) => (
              <tr key={request.codpeticiones} className="hover:bg-slate-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <EstadoBadge codestado={request.codestado} />
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-slate-900 max-w-md">{request.description}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-slate-600">
                    {request.solucion ? (
                      <span className="max-w-md">{request.solucion}</span>
                    ) : (
                      <span className="text-slate-400 italic">Sin solución aún</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {formatDate(request.fesolicita)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {formatDate(request.fesolucion)}
                </td>
                <td className="px-6 py-4">
                  {request.ai_classification_data ? (
                    <AIClassificationBadge data={request.ai_classification_data} />
                  ) : (
                    <span className="text-xs text-slate-400 italic">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Vista Mobile: Cards */}
      <div className="md:hidden divide-y divide-slate-200">
        {requests.map((request) => (
          <div key={request.codpeticiones} className="p-4">
            <div className="flex items-start justify-between mb-2">
              <EstadoBadge codestado={request.codestado} />
            </div>
            <div className="mb-2">
              <p className="text-sm font-medium text-slate-900 mb-1">Descripción</p>
              <p className="text-sm text-slate-600">{request.description}</p>
            </div>
            {request.solucion && (
              <div className="mb-2">
                <p className="text-sm font-medium text-slate-900 mb-1">Solución</p>
                <p className="text-sm text-slate-600">{request.solucion}</p>
              </div>
            )}
            <div className="text-xs text-slate-500 space-y-1">
              <p>Creada: {formatDate(request.fesolicita)}</p>
              {request.fesolucion && <p>Solucionada: {formatDate(request.fesolucion)}</p>}
            </div>
            {request.ai_classification_data && (
              <div className="mt-2 pt-2 border-t border-slate-200">
                <p className="text-xs font-medium text-slate-900 mb-1">Clasificación IA</p>
                <AIClassificationBadge data={request.ai_classification_data} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Controles de Paginación */}
      {pagination.total > 0 && (
        <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentOffset === 0}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Anterior
          </button>

          <span className="text-sm text-slate-600">
            Página {Math.floor(currentOffset / limit) + 1} de{' '}
            {Math.ceil(pagination.total / limit) || 1}
          </span>

          <button
            onClick={handleNext}
            disabled={!pagination.has_more}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Siguiente
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

