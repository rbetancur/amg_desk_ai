from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import jwt, JWTError
from email_validator import validate_email, EmailNotValidError
from app.core.config import settings
from app.core.exceptions import create_error_response

security = HTTPBearer(auto_error=False)


async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """
    Dependency para validar API Key.
    Acepta API Key desde:
    - Header Authorization: Bearer <key>
    - Header X-API-Key
    """
    api_key = None

    # Intentar obtener desde Authorization Bearer
    if credentials and credentials.credentials:
        api_key = credentials.credentials
    # Intentar obtener desde X-API-Key header
    elif x_api_key:
        api_key = x_api_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                error_code="api_key_required",
                message="API Key requerida para acceder a este recurso.",
                detail="API Key no proporcionada",
                action_suggestion="Proporciona la API Key en el header 'Authorization: Bearer <key>' o 'X-API-Key: <key>'.",
            ),
        )

    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                error_code="invalid_api_key",
                message="La API Key proporcionada no es válida.",
                detail="API Key inválida",
                action_suggestion="Verifica que la API Key sea correcta y esté configurada adecuadamente.",
            ),
        )

    return api_key


def extract_username_from_email(email: str) -> str:
    """
    Extrae el username del email (parte antes de @).
    
    Args:
        email: Email del usuario
        
    Returns:
        str: Username extraído
        
    Raises:
        ValueError: Si el formato de email es inválido o el username excede 25 caracteres
    """
    # Validar formato de email
    try:
        validate_email(email)
    except EmailNotValidError:
        raise ValueError("Formato de email inválido")
    
    # Extraer username
    username = email.split("@")[0]
    
    # Validar longitud (NO truncar)
    if len(username) > 25:
        raise ValueError(f"Username '{username}' excede 25 caracteres (límite: 25)")
    
    return username


def verify_supabase_jwt(token: str) -> dict:
    """
    Valida token JWT de Supabase usando SUPABASE_JWT_SECRET.
    
    Los tokens JWT de Supabase se firman con el JWT Secret, no con la ANON_KEY.
    El JWT Secret se puede obtener desde: Dashboard > Settings > API > JWT Secret
    
    Args:
        token: Token JWT a validar
        
    Returns:
        dict: Payload del token decodificado
        
    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    # Preferir JWT_SECRET sobre ANON_KEY para validar tokens
    jwt_secret = settings.SUPABASE_JWT_SECRET or settings.SUPABASE_ANON_KEY
    
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                error_code="jwt_secret_not_configured",
                message="Error de configuración del servidor.",
                detail="SUPABASE_JWT_SECRET o SUPABASE_ANON_KEY no configurada",
                action_suggestion="Contacta al administrador del sistema.",
            ),
        )
    
    try:
        # Intentar validar con HS256 (algoritmo usado por Supabase para JWT Secret)
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                error_code="invalid_token",
                message="Tu sesión ha expirado o el token es inválido. Por favor, inicia sesión nuevamente.",
                detail=f"Error de validación JWT: {str(e)}",
                action_suggestion="Haz clic en 'Iniciar Sesión' para autenticarte nuevamente.",
            ),
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Dependency para obtener el usuario autenticado desde JWT de Supabase.
    Extrae el username del email y valida que no exceda 25 caracteres.
    
    Returns:
        dict: Información del usuario con 'ususolicita' (username extraído del email)
        
    Raises:
        HTTPException: Si el token es inválido, el email es inválido o el username excede 25 caracteres
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                error_code="token_required",
                message="Token JWT requerido para acceder a este recurso.",
                detail="Token JWT no proporcionado",
                action_suggestion="Proporciona el token JWT en el header 'Authorization: Bearer <token>'.",
            ),
        )
    
    token = credentials.credentials
    
    # Validar JWT
    payload = verify_supabase_jwt(token)
    
    # Extraer email del token
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=create_error_response(
                error_code="email_not_found",
                message="El email no se encontró en el token de autenticación.",
                detail="Email no encontrado en el token",
                action_suggestion="Inicia sesión nuevamente para obtener un token válido.",
            ),
        )
    
    # Validar formato de email
    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=create_error_response(
                error_code="invalid_email_format",
                message="El formato del email en el token no es válido.",
                detail="Formato de email inválido",
                action_suggestion="Contacta al administrador del sistema para resolver este problema.",
            ),
        )
    
    # Extraer username del email
    try:
        ususolicita = extract_username_from_email(email)
    except ValueError as e:
        error_msg = str(e)
        if "excede 25 caracteres" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=create_error_response(
                    error_code="username_too_long",
                    message="El nombre de usuario extraído del email excede el límite permitido de 25 caracteres.",
                    detail=error_msg,
                    action_suggestion="Contacta al administrador del sistema para resolver este problema.",
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=create_error_response(
                    error_code="username_extraction_error",
                    message="No se pudo extraer el nombre de usuario del email.",
                    detail=error_msg,
                    action_suggestion="Verifica que el email tenga un formato válido.",
                ),
            )
    
    # Retornar información del usuario
    return {
        "sub": payload.get("sub"),  # User ID (UUID)
        "email": email,
        "ususolicita": ususolicita,  # Username extraído del email
    }

