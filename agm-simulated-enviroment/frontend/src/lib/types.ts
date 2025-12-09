// Tipos TypeScript para datos de Supabase
// Mapeo desde nombres legacy en BD (español) a nombres en inglés en código

export interface Category {
  codcategoria: number
  categoria: string
}

export interface AIClassificationData {
  app_type: 'amerika' | 'dominio'
  confidence: number // 0.0 - 1.0
  classification_timestamp: string // ISO8601
  detected_actions: string[]
  raw_classification?: string
}

export interface Request {
  codpeticiones: number
  codcategoria: number
  codestado: number | null // 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO
  codprioridad: number | null
  codgravedad: number | null
  codfrecuencia: number | null
  ususolicita: string
  fesolicita: string // ISO datetime string
  description: string
  solucion: string | null
  fesolucion: string | null // ISO datetime string
  codusolucion: string | null
  codgrupo: number | null
  oportuna: string | null
  feccierre: string | null // ISO datetime string
  codmotcierre: number | null
  ai_classification_data: AIClassificationData | null
}

export interface RequestCreate {
  codcategoria: number
  description: string
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
}

