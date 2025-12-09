import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { supabase } from '../api_services/supabase_client'
import type { User, Session } from '@supabase/supabase-js'
import * as authService from '../api_services/auth'
import type { AuthResponse } from '../api_services/auth'
import { handleApiError } from '../lib/error-handler'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  error: Error | null
  signIn: (email: string, password: string) => Promise<AuthResponse>
  signUp: (email: string, password: string) => Promise<AuthResponse>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Cargar sesión inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Escuchar cambios de autenticación
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string): Promise<AuthResponse> => {
    setError(null)
    try {
      const response = await authService.signIn(email, password)
      if (response.error) {
        const errorMessage = handleApiError(response.error)
        setError(new Error(errorMessage))
      }
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(new Error(errorMessage))
      throw err
    }
  }

  const signUp = async (email: string, password: string): Promise<AuthResponse> => {
    setError(null)
    try {
      const response = await authService.signUp(email, password)
      if (response.error) {
        const errorMessage = handleApiError(response.error)
        setError(new Error(errorMessage))
      }
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(new Error(errorMessage))
      throw err
    }
  }

  const signOut = async (): Promise<void> => {
    setError(null)
    try {
      const { error } = await authService.signOut()
      if (error) {
        const errorMessage = handleApiError(error)
        setError(new Error(errorMessage))
        throw error
      }
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(new Error(errorMessage))
      throw err
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        error,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

