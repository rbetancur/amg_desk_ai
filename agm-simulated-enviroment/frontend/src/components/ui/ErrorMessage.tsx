import { AlertCircle, LogIn } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface ErrorMessageProps {
  message: string
  actionSuggestion?: string
  showLoginButton?: boolean
}

export function ErrorMessage({ message, actionSuggestion, showLoginButton }: ErrorMessageProps) {
  const navigate = useNavigate()
  const isUnauthorized = message.toLowerCase().includes('sesión') || 
                         message.toLowerCase().includes('autorizado') ||
                         message.toLowerCase().includes('401') ||
                         showLoginButton

  const handleLogin = () => {
    navigate('/login')
  }

  return (
    <div className="p-3 bg-red-50 border border-red-200 rounded-md">
      <p className="text-sm text-red-600 flex items-center gap-2">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        {message}
      </p>
      {actionSuggestion && (
        <p className="text-sm text-red-500 mt-2 ml-6">
          💡 {actionSuggestion}
        </p>
      )}
      {isUnauthorized && (
        <button
          onClick={handleLogin}
          className="mt-3 ml-6 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
        >
          <LogIn className="w-4 h-4" />
          Ir a Iniciar Sesión
        </button>
      )}
    </div>
  )
}

