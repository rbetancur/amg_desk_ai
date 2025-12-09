"""
Servicio para generación de contraseñas seguras.
Implementa funciones específicas para Amerika y Dominio según sus requisitos.
"""
import secrets
import string
from typing import Optional


def generate_password_amerika() -> str:
    """
    Genera una contraseña alfanumérica para Amerika.
    
    Requisitos:
    - Longitud: aleatoria entre 10 y 25 caracteres (inclusive)
    - Caracteres: letras minúsculas (a-z), mayúsculas (A-Z), números (0-9)
    - Debe contener al menos una letra y un número
    
    Returns:
        str: Contraseña generada
    """
    # Caracteres permitidos
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    all_chars = lowercase + uppercase + digits
    
    # Longitud aleatoria entre 10 y 25
    length = secrets.randbelow(16) + 10  # 10-25 inclusive
    
    # Generar contraseña asegurando que tenga al menos una letra y un número
    max_attempts = 10
    for _ in range(max_attempts):
        password = "".join(secrets.choice(all_chars) for _ in range(length))
        
        # Verificar que tenga al menos una letra y un número
        has_letter = any(c in password for c in lowercase + uppercase)
        has_digit = any(c in password for c in digits)
        
        if has_letter and has_digit:
            return password
    
    # Si después de 10 intentos no se cumple, generar una garantizada
    # Tomar al menos una letra y un número, luego completar
    password_chars = [
        secrets.choice(lowercase + uppercase),  # Al menos una letra
        secrets.choice(digits),  # Al menos un número
    ]
    # Completar con caracteres aleatorios
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - 2))
    # Mezclar los caracteres
    secrets.SystemRandom().shuffle(password_chars)
    
    return "".join(password_chars)


def generate_password_dominio() -> str:
    """
    Genera una contraseña para Dominio corporativo.
    
    Requisitos:
    - Longitud: mínimo 10 caracteres, recomendado 12-16
    - Debe incluir al menos: una mayúscula, una minúscula y un número
    - Símbolos opcionales (*.?!#&$) con probabilidad 30%
    
    Returns:
        str: Contraseña generada
    """
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "*.?!#&$"
    
    # Longitud recomendada entre 12 y 16 caracteres
    length = secrets.randbelow(5) + 12  # 12-16 inclusive
    
    max_attempts = 10
    for attempt in range(max_attempts):
        password_chars = []
        
        # Garantizar al menos una mayúscula, minúscula y número
        password_chars.append(secrets.choice(uppercase))
        password_chars.append(secrets.choice(lowercase))
        password_chars.append(secrets.choice(digits))
        
        # Completar el resto
        all_chars = lowercase + uppercase + digits
        
        # Decidir si incluir símbolos (30% de probabilidad)
        include_symbols = secrets.randbelow(100) < 30
        
        if include_symbols:
            all_chars += symbols
            # Agregar al menos un símbolo
            password_chars.append(secrets.choice(symbols))
            remaining = length - 4
        else:
            remaining = length - 3
        
        # Completar con caracteres aleatorios
        password_chars.extend(secrets.choice(all_chars) for _ in range(remaining))
        
        # Mezclar los caracteres
        secrets.SystemRandom().shuffle(password_chars)
        password = "".join(password_chars)
        
        # Validar requisitos
        has_uppercase = any(c in password for c in uppercase)
        has_lowercase = any(c in password for c in lowercase)
        has_digit = any(c in password for c in digits)
        
        if has_uppercase and has_lowercase and has_digit:
            return password
    
    # Si después de 10 intentos no se cumple, generar una garantizada
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
    ]
    # Completar con caracteres aleatorios
    all_chars = lowercase + uppercase + digits
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - 3))
    secrets.SystemRandom().shuffle(password_chars)
    
    return "".join(password_chars)

