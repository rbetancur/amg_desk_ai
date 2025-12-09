import { useAuth } from '../contexts/AuthContext'
import { extractUsernameFromEmail } from '../api_services/auth'
import { supabase } from '../api_services/supabase_client'

export function useSupabaseAuth() {
  const { user, session, loading, signIn, signUp, signOut } = useAuth()

  const isAuthenticated = !!user

  const username = user?.email ? extractUsernameFromEmail(user.email) : null

  const getAuthToken = async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token ?? null
  }

  return {
    user,
    session,
    loading,
    isAuthenticated,
    username,
    signIn,
    signUp,
    signOut,
    getAuthToken,
  }
}

