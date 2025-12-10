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
  codcategoria: z
    .preprocess(
      (val) => {
        // Manejar valores vacíos, undefined, null o NaN
        if (val === '' || val === null || val === undefined) {
          return undefined
        }
        // Si es NaN (cuando valueAsNumber convierte string vacío)
        if (typeof val === 'number' && isNaN(val)) {
          return undefined
        }
        // Convertir string a number si es necesario
        if (typeof val === 'string' && val !== '') {
          const num = Number(val)
          return isNaN(num) ? undefined : num
        }
        return val
      },
      z
        .number({
          required_error: 'Debes seleccionar una categoría',
          invalid_type_error: 'Debes seleccionar una categoría válida',
        })
        .refine(
          (val) => val === 300 || val === 400,
          {
            message: 'Debes seleccionar una categoría de la lista',
          }
        )
    ),
  description: z
    .string({
      required_error: 'La descripción es requerida',
    })
    .min(1, 'La descripción del problema es requerida. Por favor, describe el problema que necesitas resolver.')
    .max(4000, 'La descripción no puede exceder 4000 caracteres. Por favor, acorta tu descripción.'),
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

