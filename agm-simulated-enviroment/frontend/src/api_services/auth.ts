import { supabase } from './supabase_client'
import type { User, Session, AuthError } from '@supabase/supabase-js'

export interface AuthResponse {
  user: User | null
  error: AuthError | null
}

/**
 * Extrae el username del email (parte antes de @)
 * Valida que no exceda 25 caracteres
 */
export function extractUsernameFromEmail(email: string): string {
  const username = email.split('@')[0]
  
  if (username.length > 25) {
    throw new Error(`Username '${username}' excede 25 caracteres (límite: 25)`)
  }
  
  return username
}

/**
 * Inicia sesión con email y contraseña
 */
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  return {
    user: data.user,
    error,
  }
}

/**
 * Registra un nuevo usuario
 */
export async function signUp(email: string, password: string): Promise<AuthResponse> {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })

  return {
    user: data.user,
    error,
  }
}

/**
 * Cierra la sesión del usuario actual
 */
export async function signOut(): Promise<{ error: AuthError | null }> {
  const { error } = await supabase.auth.signOut()
  return { error }
}

/**
 * Obtiene el usuario actual
 */
export async function getCurrentUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

/**
 * Obtiene la sesión actual
 */
export async function getSession(): Promise<Session | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

