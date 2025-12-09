import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl && !supabaseAnonKey) {
  throw new Error('Configuración incompleta: faltan las variables de entorno VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY. Por favor, verifica tu archivo .env')
}

if (!supabaseUrl) {
  throw new Error('Configuración incompleta: falta la variable de entorno VITE_SUPABASE_URL. Por favor, verifica tu archivo .env')
}

if (!supabaseAnonKey) {
  throw new Error('Configuración incompleta: falta la variable de entorno VITE_SUPABASE_ANON_KEY. Por favor, verifica tu archivo .env')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

