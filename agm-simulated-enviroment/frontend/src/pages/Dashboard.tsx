import { LogOut, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { RequestForm } from '../features/requests/RequestForm'
import { RequestTable } from '../features/requests/RequestTable'
import { useSupabaseAuth } from '../hooks/useSupabaseAuth'

export function Dashboard() {
  const { user, signOut } = useSupabaseAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    try {
      await signOut()
      navigate('/login')
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">Mesa de Servicio</h1>
              <p className="text-sm text-slate-600 mt-1">
                {user?.email && (
                  <span className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    {user.email}
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Formulario de Solicitud */}
          <RequestForm />

          {/* Tabla de Solicitudes */}
          <RequestTable />
        </div>
      </main>
    </div>
  )
}

