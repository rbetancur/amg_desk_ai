import { useEffect } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale/es'
import { X, Calendar, User, FileText, CheckCircle, AlertCircle, Clock, Brain, Tag } from 'lucide-react'
import type { Request } from '../../lib/types'
import { getEstadoText, getCategoryName, getPrioridadText, getGravedadText, getFrecuenciaText } from '../../lib/constants'

interface RequestDetailModalProps {
  request: Request | null
  isOpen: boolean
  onClose: () => void
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'N/A'
  try {
    return format(new Date(dateString), 'dd MMM yyyy, HH:mm', { locale: es })
  } catch {
    return dateString
  }
}

function DetailRow({ label, value, icon: Icon }: { label: string; value: string | number | null; icon?: React.ComponentType<{ className?: string }> }) {
  const displayValue = value === null || value === undefined ? 'N/A' : String(value)
  
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-b-0">
      {Icon && (
        <div className="flex-shrink-0 mt-0.5">
          <Icon className="w-4 h-4 text-slate-400" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <dt className="text-sm font-medium text-slate-700 mb-1">{label}</dt>
        <dd className="text-sm text-slate-900 break-words">{displayValue}</dd>
      </div>
    </div>
  )
}

export function RequestDetailModal({ request, isOpen, onClose }: RequestDetailModalProps) {
  // Cerrar modal con tecla ESC
  useEffect(() => {
    if (!isOpen) return

    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    // Prevenir scroll del body cuando el modal está abierto
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen || !request) return null

  const estado = request.codestado ?? 1
  const estadoText = getEstadoText(estado)

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Container */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
            <h2
              id="modal-title"
              className="text-xl font-semibold text-slate-900"
            >
              Detalles de la Solicitud
            </h2>
            <button
              onClick={onClose}
              className="rounded-md p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
              aria-label="Cerrar modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <dl className="space-y-0">
              {/* ID de Solicitud */}
              <DetailRow
                label="ID de Solicitud"
                value={`#${request.codpeticiones}`}
                icon={Tag}
              />

              {/* Categoría */}
              <DetailRow
                label="Categoría"
                value={getCategoryName(request.codcategoria)}
                icon={Tag}
              />

              {/* Estado */}
              <div className="flex items-start gap-3 py-3 border-b border-slate-100">
                <div className="flex-shrink-0 mt-0.5">
                  <AlertCircle className="w-4 h-4 text-slate-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <dt className="text-sm font-medium text-slate-700 mb-1">Estado</dt>
                  <dd>
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full border ${
                        estado === 1
                          ? 'bg-amber-100 text-amber-800 border-amber-200'
                          : estado === 2
                          ? 'bg-blue-100 text-blue-800 border-blue-200'
                          : 'bg-emerald-100 text-emerald-800 border-emerald-200'
                      }`}
                    >
                      {estado === 1 && <AlertCircle className="w-3 h-3" />}
                      {estado === 2 && <Clock className="w-3 h-3" />}
                      {estado === 3 && <CheckCircle className="w-3 h-3" />}
                      {estadoText}
                    </span>
                  </dd>
                </div>
              </div>

              {/* Usuario que solicita */}
              <DetailRow
                label="Usuario que Solicita"
                value={request.ususolicita}
                icon={User}
              />

              {/* Fecha de Creación */}
              <DetailRow
                label="Fecha de Creación"
                value={formatDate(request.fesolicita)}
                icon={Calendar}
              />

              {/* Prioridad, Gravedad, Frecuencia */}
              {request.codprioridad !== null && (
                <DetailRow
                  label="Prioridad"
                  value={getPrioridadText(request.codprioridad)}
                />
              )}

              {request.codgravedad !== null && (
                <DetailRow
                  label="Gravedad"
                  value={getGravedadText(request.codgravedad)}
                />
              )}

              {request.codfrecuencia !== null && (
                <DetailRow
                  label="Frecuencia"
                  value={getFrecuenciaText(request.codfrecuencia)}
                />
              )}

              {/* Descripción */}
              <div className="flex items-start gap-3 py-3 border-b border-slate-100">
                <div className="flex-shrink-0 mt-0.5">
                  <FileText className="w-4 h-4 text-slate-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <dt className="text-sm font-medium text-slate-700 mb-1">Descripción</dt>
                  <dd className="text-sm text-slate-900 whitespace-pre-wrap break-words">
                    {request.description}
                  </dd>
                </div>
              </div>

              {/* Solución */}
              {request.solucion && (
                <div className="flex items-start gap-3 py-3 border-b border-slate-100">
                  <div className="flex-shrink-0 mt-0.5">
                    <CheckCircle className="w-4 h-4 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <dt className="text-sm font-medium text-slate-700 mb-1">Solución</dt>
                    <dd className="text-sm text-slate-900 whitespace-pre-wrap break-words">
                      {request.solucion}
                    </dd>
                  </div>
                </div>
              )}

              {/* Fecha de Solución */}
              {request.fesolucion && (
                <DetailRow
                  label="Fecha de Solución"
                  value={formatDate(request.fesolucion)}
                  icon={Calendar}
                />
              )}

              {/* Usuario que Resolvió */}
              {request.codusolucion && (
                <DetailRow
                  label="Usuario que Resolvió"
                  value={request.codusolucion}
                  icon={User}
                />
              )}

              {/* Fecha de Cierre */}
              {request.feccierre && (
                <DetailRow
                  label="Fecha de Cierre"
                  value={formatDate(request.feccierre)}
                  icon={Calendar}
                />
              )}

              {/* Datos de Clasificación IA */}
              {request.ai_classification_data && (
                <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-b-0">
                  <div className="flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <dt className="text-sm font-medium text-slate-700 mb-2">Clasificación IA</dt>
                    <dd className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full border ${
                            request.ai_classification_data.app_type === 'amerika'
                              ? 'bg-purple-100 text-purple-800 border-purple-200'
                              : 'bg-indigo-100 text-indigo-800 border-indigo-200'
                          }`}
                        >
                          <Brain className="w-3 h-3" />
                          {request.ai_classification_data.app_type === 'amerika' ? 'Amerika' : 'Dominio'}
                        </span>
                        <span className="text-xs text-slate-600">
                          {Math.round(request.ai_classification_data.confidence * 100)}% confianza
                        </span>
                      </div>
                      {request.ai_classification_data.detected_actions.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-slate-700 mb-1">Acciones Detectadas:</p>
                          <ul className="list-disc list-inside text-xs text-slate-600 space-y-1">
                            {request.ai_classification_data.detected_actions.map((action, idx) => (
                              <li key={idx}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {request.ai_classification_data.classification_timestamp && (
                        <p className="text-xs text-slate-500 mt-2">
                          Clasificado: {formatDate(request.ai_classification_data.classification_timestamp)}
                        </p>
                      )}
                    </dd>
                  </div>
                </div>
              )}
            </dl>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

