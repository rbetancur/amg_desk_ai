import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSupabaseAuth } from '../hooks/useSupabaseAuth'

export function HomePage() {
  const { isAuthenticated, loading } = useSupabaseAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        navigate('/dashboard', { replace: true })
      } else {
        navigate('/login', { replace: true })
      }
    }
  }, [isAuthenticated, loading, navigate])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-slate-600">Cargando...</div>
    </div>
  )
}

