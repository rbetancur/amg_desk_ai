import type { AuthError } from '@supabase/supabase-js'

/**
 * Verifica si un error es de tipo API
 */
export function isApiError(error: unknown): boolean {
  return error instanceof Error || (typeof error === 'object' && error !== null && 'message' in error)
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
      return 'Sesión expirada. Por favor, inicia sesión nuevamente.'
    }
    if (errorMessage.includes('403') || errorMessage.includes('forbidden')) {
      return 'No tienes permisos para realizar esta acción.'
    }
    if (errorMessage.includes('404') || errorMessage.includes('not found')) {
      return 'Recurso no encontrado.'
    }
    if (errorMessage.includes('422') || errorMessage.includes('validation') || errorMessage.includes('unprocessable')) {
      return 'Datos inválidos. Verifica la información ingresada.'
    }
    if (errorMessage.includes('500') || errorMessage.includes('internal server error')) {
      return 'Error del servidor. Por favor, intenta más tarde.'
    }
    if (errorMessage.includes('503') || errorMessage.includes('service unavailable')) {
      return 'El servicio no está disponible temporalmente. Por favor, intenta más tarde.'
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

