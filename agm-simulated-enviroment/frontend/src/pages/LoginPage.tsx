import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LoginForm } from '../features/auth/LoginForm'
import { useSupabaseAuth } from '../hooks/useSupabaseAuth'

export function LoginPage() {
  const { isAuthenticated, loading } = useSupabaseAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-600">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <LoginForm />
    </div>
  )
}

