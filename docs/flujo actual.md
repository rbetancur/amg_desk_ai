# Flujo actual de atención a mesas de servicio para gestión de accesos

El proceso de atención de solicitudes relacionadas con cuentas de acceso (Dominio y Amerika) depende completamente de una auxiliar que debe interpretar manualmente cada mesa de servicio, debe validar su categoría, identificar el problema real, ejecutar acciones técnicas a través de múltiples APIs, documentar la resolución y comunicar el resultado al funcionario.

Flujo es el siguiente:

# 1. Recepción de la mesa de servicio

- Un funcionario crea una mesa de servicio en la plataforma, indicando:
    - Su usuario
    - Una categoría seleccionada (por ahora: “Amerika” o “Cambio de contraseña” se usan para solicitudes de desbloqueo de cuenta o cambio de contraseña en cualquiera de los dos dominios)
    - Una descripción del problema

# 2. Lectura y análisis manual

La auxiliar revisa la mesa recién creada y lee la descripción para entender realmente qué necesita el usuario. La auxiliar solo puede solucionar dos tipos de mesa de servicio:
- Cambio de contraseña de Amerika o de cuenta de dominio
- Desbloquear la cuenta de Amerika o de cuenta de dominio

# 3. Validación de la categoría

La auxiliar compara lo que el usuario escribió con la categoría que seleccionó.
- Si coinciden, continúa.
- Si no coinciden, corrige la categorización antes de procesar.

# 4. Identificación del tipo de solicitud

La auxiliar determina, según el texto del funcionario, si la necesidad es:
- Desbloquear una cuenta
- Cambiar/generar una contraseña nueva
- Ambas

# 5. Determinación del tipo de cuenta afectada

La auxiliar interpreta si la solicitud corresponde a:

- Cuenta de Dominio (corporativa): correo, inicio de sesión general, servicios internos
- Aplicación Amerika: credenciales específicas de esa aplicación

# 6. Ejecución de la acción correspondiente

Según la clasificación, la auxiliar utiliza herramientas distintas:

## Para Cuentas de Dominio:
- Consultar el usuario por nombre de funcionario que registra la solicitud
- Cambiar contraseña
- Desbloquear la cuenta
- Bloquear cuentas o procesar novedades (Fuera del alcance del agente)
- Todo a través de APIs o sistemas propios del dominio corporativo.

# 7. Para Cuentas de Amerika:

- Generar nueva contraseña
- Bloquear o desbloquear su acceso
- Todo con APIs diferentes a las del dominio.

# 8. Obtención de resultados

Después de ejecutar la acción (por ejemplo, generar una nueva contraseña), la auxiliar obtiene:

- Confirmación de éxito o error
- La contraseña nueva (si aplica)

# 9. Actualización y documentación de la mesa de servicio

La auxiliar documenta en la mesa:

- Qué se hizo
- Qué APIs se usaron
- Resultados
- Evidencias

# 10. Comunicación al funcionario

Finalmente, la auxiliar cambia el estado de la mesa de servicio, y  redacta un mensaje formal:

- Indicando qué se realizó
- Incluyendo la contraseña nueva si corresponde
- Dando instrucciones adicionales si son necesarias

# 11. Luego este mensaje es enviado por la mesa de servicio  al funcionario por correo electrónico cuando la mesa de servicio es resuelta.
