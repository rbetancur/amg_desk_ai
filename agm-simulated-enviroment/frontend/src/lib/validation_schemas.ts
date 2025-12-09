import { z } from 'zod'

// Esquema de validación para autenticación
export const signInSchema = z.object({
  email: z.string().min(1, 'El email es requerido').email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida').min(6, 'La contraseña debe tener al menos 6 caracteres'),
})

export const signUpSchema = z.object({
  email: z.string().min(1, 'El email es requerido').email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida').min(6, 'La contraseña debe tener al menos 6 caracteres'),
  confirmPassword: z.string().min(1, 'La confirmación de contraseña es requerida'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
})

// Esquema de validación para crear solicitud
export const requestCreateSchema = z.object({
  codcategoria: z.number().refine((val) => val === 300 || val === 400, {
    message: 'La categoría debe ser 300 o 400',
  }),
  description: z
    .string()
    .min(1, 'La descripción es requerida')
    .max(4000, 'La descripción no puede exceder 4000 caracteres'),
})

// Esquema para categoría
export const categorySchema = z.object({
  codcategoria: z.number(),
  categoria: z.string(),
})

export type SignInInput = z.infer<typeof signInSchema>
export type SignUpInput = z.infer<typeof signUpSchema>
export type RequestCreateInput = z.infer<typeof requestCreateSchema>
export type Category = z.infer<typeof categorySchema>

