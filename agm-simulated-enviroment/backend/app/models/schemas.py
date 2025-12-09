from datetime import datetime
from typing import Optional, Literal, List, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar("T")


class CategoryBase(BaseModel):
    """Esquema base para Category"""

    codcategoria: int = Field(..., description="Código de la categoría")
    categoria: str = Field(..., max_length=50, description="Nombre de la categoría")


class CategoryCreate(CategoryBase):
    """Esquema para crear una categoría"""

    pass


class CategoryResponse(CategoryBase):
    """Esquema de respuesta para Category"""

    class Config:
        from_attributes = True


class RequestBase(BaseModel):
    """Esquema base para Request"""

    codcategoria: int = Field(..., description="Código de la categoría")
    description: str = Field(..., min_length=1, max_length=4000, description="Descripción del problema")


class RequestCreate(RequestBase):
    """Esquema para crear una solicitud"""

    pass


class RequestUpdate(BaseModel):
    """Esquema para actualizar una solicitud"""

    codestado: Optional[int] = Field(
        None, description="Estado: 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO"
    )
    solucion: Optional[str] = Field(None, description="Solución al problema")
    fesolucion: Optional[datetime] = Field(None, description="Fecha de solución")
    codusolucion: Optional[str] = Field(
        None, max_length=24, description="Código del usuario que resuelve"
    )
    feccierre: Optional[datetime] = Field(None, description="Fecha de cierre")
    codmotcierre: Optional[int] = Field(None, description="Motivo de cierre")
    ai_classification_data: Optional[dict] = Field(
        None, description="Datos de clasificación de la IA"
    )


class RequestResponse(BaseModel):
    """Esquema de respuesta para Request"""

    codpeticiones: int
    codcategoria: int
    codestado: Optional[int] = None
    codprioridad: Optional[int] = None
    codgravedad: Optional[int] = None
    codfrecuencia: Optional[int] = None
    ususolicita: str
    fesolicita: datetime
    description: str
    solucion: Optional[str] = None
    fesolucion: Optional[datetime] = None
    codusolucion: Optional[str] = None
    codgrupo: Optional[int] = None
    oportuna: Optional[str] = None
    feccierre: Optional[datetime] = None
    codmotcierre: Optional[int] = None
    ai_classification_data: Optional[dict] = None

    class Config:
        from_attributes = True


# ============================================================================
# Esquemas para Endpoints de Acción (Amerika y Dominio)
# ============================================================================

# Amerika Schemas
class AmerikaPasswordResult(BaseModel):
    """Esquema para el resultado de generate_password de Amerika"""
    password_length: int = Field(..., description="Longitud de la contraseña generada")
    generated_at: str = Field(..., description="Timestamp ISO8601 de generación")


class AmerikaAccountResult(BaseModel):
    """Esquema para el resultado de unlock_account/lock_account de Amerika"""
    account_status: Literal["unlocked", "locked"] = Field(..., description="Estado de la cuenta")
    action_timestamp: str = Field(..., description="Timestamp ISO8601 de la acción")


class AmerikaActionRequest(BaseModel):
    """Esquema para request de acciones de Amerika"""
    user_id: str = Field(..., description="ID del usuario")
    action_type: Literal["generate_password", "unlock_account", "lock_account"] = Field(
        ..., description="Tipo de acción a ejecutar"
    )


class AmerikaActionResponse(BaseModel):
    """Esquema para respuesta de acciones de Amerika"""
    success: bool = Field(..., description="Indica si la acción fue exitosa")
    action_type: str = Field(..., description="Tipo de acción ejecutada")
    result: dict = Field(..., description="Resultado de la acción")
    message: str = Field(..., description="Mensaje descriptivo")
    generated_password: Optional[str] = Field(
        None, description="Contraseña generada (solo presente si action_type genera contraseña)"
    )


# Dominio Schemas
class DominioFindUserResult(BaseModel):
    """Esquema para el resultado de find_user de Dominio"""
    user_id: Optional[str] = Field(None, description="ID del usuario encontrado")
    user_name: str = Field(..., description="Nombre de usuario buscado")
    email: Optional[str] = Field(None, description="Email del usuario")
    status: Optional[str] = Field(None, description="Estado del usuario")
    found: bool = Field(..., description="Indica si el usuario fue encontrado")


class DominioPasswordResult(BaseModel):
    """Esquema para el resultado de change_password de Dominio"""
    password_length: int = Field(..., description="Longitud de la contraseña generada")
    changed_at: str = Field(..., description="Timestamp ISO8601 del cambio")


class DominioAccountResult(BaseModel):
    """Esquema para el resultado de unlock_account de Dominio"""
    account_status: Literal["unlocked"] = Field(..., description="Estado de la cuenta")
    action_timestamp: str = Field(..., description="Timestamp ISO8601 de la acción")


class DominioActionRequest(BaseModel):
    """Esquema para request de acciones de Dominio"""
    user_id: str = Field(..., description="ID del usuario")
    action_type: Literal["find_user", "change_password", "unlock_account"] = Field(
        ..., description="Tipo de acción a ejecutar"
    )
    user_name: Optional[str] = Field(None, description="Nombre de usuario (requerido para find_user)")


class DominioActionResponse(BaseModel):
    """Esquema para respuesta de acciones de Dominio"""
    success: bool = Field(..., description="Indica si la acción fue exitosa")
    action_type: str = Field(..., description="Tipo de acción ejecutada")
    result: dict = Field(..., description="Resultado de la acción")
    message: str = Field(..., description="Mensaje descriptivo")
    generated_password: Optional[str] = Field(
        None, description="Contraseña generada (solo presente si action_type genera contraseña)"
    )


# ============================================================================
# Esquemas para Mesa de Servicio (CRUD)
# ============================================================================

# Esquema de Clasificación de IA
class AIClassificationData(BaseModel):
    """Esquema para datos de clasificación de la IA"""
    app_type: Literal["amerika", "dominio"] = Field(..., description="Tipo de aplicación detectada")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza (0.0-1.0)")
    classification_timestamp: str = Field(..., description="Timestamp ISO8601 de la clasificación")
    detected_actions: List[str] = Field(..., description="Lista de acciones detectadas")
    raw_classification: Optional[str] = Field(None, description="Texto original de clasificación para auditoría")


# Esquemas de Paginación
class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    limit: int = Field(default=50, ge=1, le=100, description="Número de items por página")
    offset: int = Field(default=0, ge=0, description="Número de items a saltar")


class PaginationMeta(BaseModel):
    """Metadatos de paginación"""
    total: int = Field(..., description="Total de items")
    limit: int = Field(..., description="Número de items por página")
    offset: int = Field(..., description="Número de items saltados")
    has_more: bool = Field(..., description="Indica si hay más items disponibles")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    items: List[T] = Field(..., description="Lista de items")
    pagination: PaginationMeta = Field(..., description="Metadatos de paginación")


# Helper functions para conversión de estados
def estado_to_text(codestado: Optional[int]) -> str:
    """
    Convierte código de estado numérico a texto.
    
    Args:
        codestado: Código de estado (1, 2, 3 o None)
        
    Returns:
        str: Texto del estado
    """
    if codestado == 1:
        return "Pendiente"
    elif codestado == 2:
        return "En Trámite"
    elif codestado == 3:
        return "Solucionado"
    else:
        return "Desconocido"


def text_to_estado(text: str) -> int:
    """
    Convierte texto de estado a código numérico.
    
    Args:
        text: Texto del estado
        
    Returns:
        int: Código de estado
    """
    estado_map = {
        "pendiente": 1,
        "en trámite": 2,
        "solucionado": 3,
    }
    return estado_map.get(text.lower(), 1)

