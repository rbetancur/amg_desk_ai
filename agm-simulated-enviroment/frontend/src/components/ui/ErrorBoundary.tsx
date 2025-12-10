import { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { handleApiError } from '../../lib/error-handler'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error capturado por ErrorBoundary:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  /**
   * Sanitiza el mensaje de error para no mostrar detalles técnicos
   */
  private sanitizeErrorMessage(error: Error | null): string {
    if (!error) {
      return 'Ocurrió un error inesperado'
    }

    const message = error.message || 'Ocurrió un error inesperado'
    
    // Filtrar detalles técnicos
    const technicalPatterns = [
      /at\s+.*\(.*\)/g, // Stack traces
      /Error:\s*/gi,
      /TypeError|ReferenceError|SyntaxError/gi,
      /http:\/\/|https:\/\//gi, // URLs
      /localhost|127\.0\.0\.1/gi, // URLs locales
      /node_modules/gi,
      /\.tsx?:\d+:\d+/gi, // Referencias a archivos
    ]

    let sanitized = message
    technicalPatterns.forEach((pattern) => {
      sanitized = sanitized.replace(pattern, '')
    })

    // Si después de sanitizar queda vacío o muy corto, usar mensaje genérico
    if (sanitized.trim().length < 10) {
      return 'Ocurrió un error inesperado. Por favor, recarga la página.'
    }

    // Usar handleApiError para obtener mensaje amigable si es posible
    try {
      const friendlyMessage = handleApiError(error)
      return friendlyMessage
    } catch {
      return sanitized.trim()
    }
  }

  render() {
    if (this.state.hasError) {
      const friendlyMessage = this.sanitizeErrorMessage(this.state.error)
      
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-slate-200 p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Algo salió mal
            </h2>
            <p className="text-sm text-slate-600 mb-6">
              {friendlyMessage}
            </p>
            <div className="space-y-2">
              <button
                onClick={this.handleReload}
                className="w-full bg-primary-600 text-white py-2 px-4 rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Recargar Página
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="w-full bg-slate-100 text-slate-700 py-2 px-4 rounded-md font-medium hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-colors"
              >
                Intentar Nuevamente
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

