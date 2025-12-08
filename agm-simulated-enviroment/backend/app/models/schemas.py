from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
    description: str = Field(..., description="Descripción del problema")


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

