import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus, AlertCircle, CheckCircle } from 'lucide-react'
import { requestCreateSchema, type RequestCreateInput } from '../../lib/validation_schemas'
import { createRequest } from '../../api_services/requests'
import { CATEGORIES } from '../../lib/constants'

interface RequestFormProps {
  onSuccess?: () => void
}

export function RequestForm({ onSuccess }: RequestFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RequestCreateInput>({
    resolver: zodResolver(requestCreateSchema),
  })

  const onSubmit = async (data: RequestCreateInput) => {
    setIsSubmitting(true)
    setError(null)
    setSuccess(false)

    try {
      await createRequest(data)
      setSuccess(true)
      reset()
      
      // Limpiar mensaje de éxito después de 3 segundos
      setTimeout(() => {
        setSuccess(false)
      }, 3000)

      // Llamar callback si existe
      if (onSuccess) {
        onSuccess()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear la solicitud')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Plus className="w-5 h-5" />
        Nueva Solicitud
      </h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="codcategoria" className="block text-sm font-medium text-slate-700 mb-1">
            Categoría
          </label>
          <select
            id="codcategoria"
            {...register('codcategoria', { valueAsNumber: true })}
            className="w-full px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">Seleccione una categoría</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.codcategoria} value={cat.codcategoria}>
                {cat.categoria}
              </option>
            ))}
          </select>
          {errors.codcategoria && (
            <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              {errors.codcategoria.message}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">
            Descripción del Problema
          </label>
          <textarea
            id="description"
            {...register('description')}
            rows={4}
            className="w-full px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 placeholder-slate-400"
            placeholder="Describe el problema que necesitas resolver..."
          />
          <div className="mt-1 flex justify-between">
            {errors.description && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.description.message}
              </p>
            )}
            <p className="text-xs text-slate-500 ml-auto">
              Máximo 4000 caracteres
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-600 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Solicitud creada exitosamente
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Creando...' : 'Crear Solicitud'}
        </button>
      </form>
    </div>
  )
}

