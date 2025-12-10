import type { AuthError } from '@supabase/supabase-js'

/**
 * Información de error extraída de respuestas del backend
 */
export interface ErrorInfo {
  message: string
  actionSuggestion?: string
}

/**
 * Verifica si un error es de tipo API
 */
export function isApiError(error: unknown): boolean {
  return error instanceof Error || (typeof error === 'object' && error !== null && 'message' in error)
}

/**
 * Extrae información de error (message y action_suggestion) de respuestas del backend
 */
export function extractErrorInfo(error: unknown): ErrorInfo {
  // Intentar extraer de respuesta del backend FastAPI
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as any).response
    if (response?.data) {
      const data = response.data
      // Verificar si tiene estructura estándar de error del backend
      if (data.message) {
        return {
          message: data.message,
          actionSuggestion: data.action_suggestion || data.actionSuggestion,
        }
      }
      // Si tiene detail como string (estructura antigua)
      if (typeof data.detail === 'string') {
        return {
          message: data.detail,
        }
      }
      // Si detail es un objeto con estructura de error
      if (typeof data.detail === 'object' && data.detail?.message) {
        return {
          message: data.detail.message,
          actionSuggestion: data.detail.action_suggestion || data.detail.actionSuggestion,
        }
      }
    }
  }

  // Fallback a manejo tradicional
  return {
    message: handleApiError(error),
  }
}

/**
 * Convierte errores de API a mensajes amigables para el usuario en español
 */
export function handleApiError(error: unknown): string {
  if (!error) {
    return 'Ocurrió un error desconocido'
  }

  // Errores de configuración (variables de entorno faltantes)
  if (error instanceof Error) {
    const errorMessage = error.message.toLowerCase()
    
    // Errores de configuración de Supabase
    if (errorMessage.includes('vite_supabase_url') || errorMessage.includes('supabase_url')) {
      return 'Error de configuración: falta la URL de Supabase. Por favor, contacta al administrador del sistema.'
    }
    if (errorMessage.includes('vite_supabase_anon_key') || errorMessage.includes('supabase_anon_key') || errorMessage.includes('anon_key')) {
      return 'Error de configuración: falta la clave de acceso de Supabase. Por favor, contacta al administrador del sistema.'
    }
    if (errorMessage.includes('configuración incompleta') || errorMessage.includes('variable de entorno')) {
      return error.message // Ya está en español
    }
    if (errorMessage.includes('missing supabase') || errorMessage.includes('environment variables')) {
      return 'Error de configuración: faltan variables de entorno de Supabase. Por favor, contacta al administrador del sistema.'
    }

    // Errores de red y conexión
    if (errorMessage.includes('network') || errorMessage.includes('fetch') || errorMessage.includes('failed to fetch')) {
      return 'Error de conexión. Verifica tu conexión a internet e intenta nuevamente.'
    }
    if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
      return 'La solicitud tardó demasiado. Por favor, intenta nuevamente.'
    }
    if (errorMessage.includes('cors')) {
      return 'Error de configuración del servidor. Por favor, contacta al administrador.'
    }

    // Errores del backend FastAPI
    if (errorMessage.includes('401') || errorMessage.includes('unauthorized')) {
      return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.'
    }
    if (errorMessage.includes('403') || errorMessage.includes('forbidden')) {
      return 'No tienes permisos para realizar esta acción. Si necesitas acceso, contacta al administrador.'
    }
    if (errorMessage.includes('404') || errorMessage.includes('not found')) {
      return 'El recurso que buscas no existe o ya fue eliminado. Regresa a la página anterior o verifica la URL.'
    }
    if (errorMessage.includes('422') || errorMessage.includes('validation') || errorMessage.includes('unprocessable')) {
      return 'Algunos campos tienen errores. Revisa los campos marcados en rojo y corrige la información antes de enviar.'
    }
    if (errorMessage.includes('500') || errorMessage.includes('internal server error')) {
      return 'Ocurrió un error en el servidor. Intenta nuevamente en unos minutos. Si el problema persiste, contacta al soporte.'
    }
    if (errorMessage.includes('503') || errorMessage.includes('service unavailable')) {
      return 'El servicio no está disponible temporalmente. Intenta nuevamente en unos minutos.'
    }
  }

  // Errores de Supabase Auth
  if (typeof error === 'object' && 'message' in error) {
    const authError = error as AuthError
    if (authError.message) {
      const authMessage = authError.message.toLowerCase()
      
      // Traducciones de errores comunes de Supabase Auth
      if (authMessage.includes('invalid login credentials') || authMessage.includes('invalid credentials')) {
        return 'Credenciales inválidas. Verifica tu email y contraseña.'
      }
      if (authMessage.includes('email already registered') || authMessage.includes('user already registered')) {
        return 'Este email ya está registrado. Inicia sesión o usa otro email.'
      }
      if (authMessage.includes('password should be at least') || authMessage.includes('password is too short')) {
        return 'La contraseña debe tener al menos 6 caracteres.'
      }
      if (authMessage.includes('invalid email') || authMessage.includes('email format is invalid')) {
        return 'El formato del email no es válido. Verifica que esté escrito correctamente.'
      }
      if (authMessage.includes('email not confirmed') || authMessage.includes('email not verified')) {
        return 'Por favor, verifica tu email antes de iniciar sesión. Revisa tu bandeja de entrada.'
      }
      if (authMessage.includes('too many requests') || authMessage.includes('rate limit')) {
        return 'Demasiados intentos. Por favor, espera unos minutos antes de intentar nuevamente.'
      }
      if (authMessage.includes('user not found')) {
        return 'Usuario no encontrado. Verifica tu email o regístrate si no tienes una cuenta.'
      }
      if (authMessage.includes('signup_disabled') || authMessage.includes('sign up disabled')) {
        return 'El registro de nuevas cuentas está deshabilitado temporalmente.'
      }
      if (authMessage.includes('token expired') || authMessage.includes('session expired')) {
        return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.'
      }
      if (authMessage.includes('jwt expired') || authMessage.includes('invalid token')) {
        return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.'
      }
      
      // Si no se encontró una traducción específica, intentar traducir el mensaje genérico
      return authError.message
    }
  }

  // Errores de Error estándar (ya procesados arriba, pero por si acaso)
  if (error instanceof Error) {
    return error.message
  }

  // Error desconocido
  return 'Ocurrió un error inesperado. Por favor, intenta nuevamente.'
}

