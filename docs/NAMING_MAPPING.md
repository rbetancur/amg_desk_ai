# Mapeo de Nomenclatura: Legacy Español ↔ Código Inglés

Este documento describe el mapeo entre los nombres legacy en español de la base de datos y los nombres modernos en inglés utilizados en el código de la aplicación.

## Principio de Retrocompatibilidad

**IMPORTANTE**: Las tablas de base de datos mantienen los nombres legacy en español (ej: `HLP_CATEGORIAS`, `HLP_PETICIONES`) para garantizar retrocompatibilidad con el sistema existente. En el código de la aplicación se utilizan nombres en inglés siguiendo estándares modernos de codificación, y los ORMs (SQLAlchemy, TypeORM) se configuran para mapear automáticamente entre los nombres en inglés del código y los nombres en español de la base de datos.

**Estructura:**
- **Base de Datos**: Nombres legacy en español (sin cambios)
- **Código**: Nombres en inglés con estándares modernos
- **Mapeo**: Configuración explícita en modelos/ORM para traducción automática

---

## Mapeo de Tablas

| Base de Datos (Legacy Español) | Código (Inglés) | Modelo SQLAlchemy | Descripción |
|--------------------------------|-----------------|-------------------|-------------|
| `HLP_CATEGORIAS` | `Category` | `Category` | Tabla de categorías de solicitudes |
| `HLP_PETICIONES` | `Request` | `Request` | Tabla principal de solicitudes |
| `HLP_DOCUMENTACION` | `Documentation` | (Opcional Fase 1) | Tabla de documentación técnica |

---

## Mapeo de Campos por Tabla

### Tabla: `HLP_CATEGORIAS` → `Category`

| Base de Datos (Legacy) | Código (Inglés) | Tipo SQLAlchemy | Tipo Python | Descripción |
|------------------------|-----------------|-----------------|-------------|-------------|
| `CODCATEGORIA` | `codcategoria` | `Integer` | `int` | Código de la categoría (PK) |
| `CATEGORIA` | `categoria` | `String(50)` | `str` | Nombre de la categoría |

**Ejemplo de uso:**
```python
# En código Python
category = Category(codcategoria=300, categoria="Cambio de Contraseña Cuenta Dominio")

# SQLAlchemy mapea automáticamente a:
# INSERT INTO "HLP_CATEGORIAS" ("CODCATEGORIA", "CATEGORIA") VALUES (300, 'Cambio de Contraseña Cuenta Dominio')
```

---

### Tabla: `HLP_PETICIONES` → `Request`

| Base de Datos (Legacy) | Código (Inglés) | Tipo SQLAlchemy | Tipo Python | Descripción |
|------------------------|-----------------|-----------------|-------------|-------------|
| `CODPETICIONES` | `codpeticiones` | `BigInteger` | `int` | Código de la solicitud (PK, autoincrement) |
| `CODCATEGORIA` | `codcategoria` | `Integer` (FK) | `int` | Código de la categoría (FK a HLP_CATEGORIAS) |
| `CODESTADO` | `codestado` | `SmallInteger` | `Optional[int]` | Estado: 1-PENDIENTE, 2-TRAMITE, 3-SOLUCIONADO (default: 1) |
| `CODPRIORIDAD` | `codprioridad` | `SmallInteger` | `Optional[int]` | Prioridad (default: 3-ALTA) |
| `CODGRAVEDAD` | `codgravedad` | `SmallInteger` | `Optional[int]` | Gravedad (default: 2-NORMAL) |
| `CODFRECUENCIA` | `codfrecuencia` | `SmallInteger` | `Optional[int]` | Frecuencia (default: 3-MUY FRECUENTE) |
| `USUSOLICITA` | `ususolicita` | `String(25)` | `str` | Código de usuario que registra la solicitud |
| `FESOLICITA` | `fesolicita` | `TIMESTAMP(timezone=True)` | `datetime` | Fecha y hora de registro (default: NOW()) |
| `DESCRIPTION` | `description` | `Text` | `str` | Descripción del problema ingresada por el usuario |
| `SOLUCION` | `solucion` | `Text` | `Optional[str]` | Respuesta que llega al usuario final |
| `FESOLUCION` | `fesolucion` | `TIMESTAMP(timezone=True)` | `Optional[datetime]` | Fecha y hora de solución |
| `CODUSOLUCION` | `codusolucion` | `String(24)` | `Optional[str]` | Código del usuario/agente que cierra (ej: 'AGENTE-MS') |
| `CODGRUPO` | `codgrupo` | `Integer` | `Optional[int]` | Grupo de atención (default: 4 - I Inmediata) |
| `OPORTUNA` | `oportuna` | `CHAR(1)` | `Optional[str]` | Oportuna (default: 'X') |
| `FECCIERRE` | `feccierre` | `TIMESTAMP(timezone=True)` | `Optional[datetime]` | Fecha y hora de cierre |
| `CODMOTCIERRE` | `codmotcierre` | `Integer` | `Optional[int]` | Motivo de cierre (default: 5-Respuesta Final) |
| `AI_CLASSIFICATION_DATA` | `ai_classification_data` | `JSONB` | `Optional[dict]` | Datos de auditoría de la IA (clasificación, confianza, tipo de aplicación) |

**Ejemplo de uso:**
```python
# En código Python
request = Request(
    codcategoria=300,
    ususolicita="user@example.com",
    description="Necesito cambiar mi contraseña de dominio",
    codestado=1  # PENDIENTE
)

# SQLAlchemy mapea automáticamente a:
# INSERT INTO "HLP_PETICIONES" ("CODCATEGORIA", "USUSOLICITA", "DESCRIPTION", "CODESTADO", ...) 
# VALUES (300, 'user@example.com', 'Necesito cambiar mi contraseña de dominio', 1, ...)
```

---

## Mapeo de Estados

### Estado de Solicitud: `CODESTADO`

| Valor Numérico (Legacy) | Texto (UI/Frontend) | Descripción |
|-------------------------|---------------------|-------------|
| `1` | `'Pendiente'` | Solicitud creada, pendiente de procesamiento |
| `2` | `'En Trámite'` | Solicitud en proceso de resolución |
| `3` | `'Solucionado'` | Solicitud resuelta y cerrada |

**Ejemplo de conversión:**
```python
# Función helper para convertir estado numérico a texto
def estado_to_text(codestado: Optional[int]) -> str:
    """Convierte CODESTADO numérico a texto legible"""
    estado_map = {
        1: "Pendiente",
        2: "En Trámite",
        3: "Solucionado"
    }
    return estado_map.get(codestado, "Desconocido")

# Uso
estado_texto = estado_to_text(request.codestado)  # "Pendiente"
```

**Nota**: El mapeo inverso (texto → numérico) también puede ser necesario en el frontend:
```typescript
// En TypeScript/Frontend
const ESTADO_MAP: Record<string, number> = {
  'Pendiente': 1,
  'En Trámite': 2,
  'Solucionado': 3
};
```

---

## Convenciones de Mapeo en SQLAlchemy

### Configuración de Mapeo Explícito

Los modelos SQLAlchemy utilizan `__tablename__` para mapear explícitamente a los nombres legacy:

```python
class Category(Base):
    """Modelo para la tabla HLP_CATEGORIAS (legacy)"""
    
    __tablename__ = "HLP_CATEGORIAS"  # Nombre legacy en BD
    
    codcategoria: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
```

### Nombres de Campos

- **En Base de Datos**: Nombres en MAYÚSCULAS (ej: `CODPETICIONES`, `USUSOLICITA`)
- **En Código Python**: Nombres en minúsculas con snake_case (ej: `codpeticiones`, `ususolicita`)
- **SQLAlchemy**: Mapea automáticamente entre ambos usando `mapped_column()`

### Relaciones

Las relaciones en SQLAlchemy utilizan nombres en inglés:

```python
class Request(Base):
    # Relación con category (nombre en inglés)
    category: Mapped["Category"] = relationship(
        "Category", back_populates="requests"
    )
```

---

## Mapeo en Esquemas Pydantic

Los esquemas Pydantic (para validación de API) mantienen los mismos nombres que los modelos SQLAlchemy:

```python
class RequestResponse(BaseModel):
    """Esquema de respuesta para Request"""
    
    codpeticiones: int
    codcategoria: int
    codestado: Optional[int] = None
    ususolicita: str
    fesolicita: datetime
    description: str
    # ... otros campos
    
    class Config:
        from_attributes = True  # Permite crear desde SQLAlchemy models
```

---

## Mapeo en Frontend (TypeScript/React)

### Tipos TypeScript

```typescript
// Tipos que reflejan la estructura legacy pero con nombres descriptivos
interface Request {
  codpeticiones: number;
  codcategoria: number;
  codestado: number | null;  // 1, 2, o 3
  ususolicita: string;
  fesolicita: string;  // ISO datetime string
  description: string;
  solucion: string | null;
  // ... otros campos
}

// Helper para convertir estado numérico a texto
const getEstadoText = (codestado: number | null): string => {
  const estados: Record<number, string> = {
    1: 'Pendiente',
    2: 'En Trámite',
    3: 'Solucionado'
  };
  return estados[codestado ?? 1] || 'Desconocido';
};
```

---

## Valores por Defecto

### Categorías (HLP_CATEGORIAS)

| CODCATEGORIA | CATEGORIA |
|--------------|-----------|
| `300` | `"Cambio de Contraseña Cuenta Dominio"` |
| `400` | `"Cambio de Contraseña Amerika"` |

### Valores por Defecto en HLP_PETICIONES

| Campo | Valor por Defecto | Descripción |
|-------|-------------------|-------------|
| `CODESTADO` | `1` | PENDIENTE |
| `CODPRIORIDAD` | `3` | ALTA |
| `CODGRAVEDAD` | `2` | NORMAL |
| `CODFRECUENCIA` | `3` | MUY FRECUENTE |
| `CODGRUPO` | `4` | I - Inmediata |
| `OPORTUNA` | `'X'` | Oportuna |
| `CODMOTCIERRE` | `5` | Respuesta Final |
| `FESOLICITA` | `NOW()` | Fecha/hora actual al crear |

---

## Notas Importantes

1. **Retrocompatibilidad**: Los nombres legacy en la base de datos NO deben cambiarse. Cualquier cambio rompería la compatibilidad con el sistema existente.

2. **Mapeo Automático**: SQLAlchemy maneja automáticamente el mapeo entre nombres de código (inglés) y nombres de BD (español) mediante `__tablename__` y `mapped_column()`.

3. **Consistencia**: Todos los modelos, schemas y tipos deben usar los mismos nombres en inglés para mantener consistencia en el código.

4. **Documentación**: Este documento debe actualizarse cuando se agreguen nuevos campos o tablas al sistema.

5. **Estados**: Los estados se manejan como números en la BD pero se convierten a texto legible en la UI. Esta conversión debe hacerse en la capa de presentación (frontend) o en helpers del backend.

---

## Referencias

- [README Principal](../docs/README.md#entidades-del-sistema) - Descripción completa de entidades
- [Plan de Desarrollo](../specs/02_dev_plan.md) - Especificación del mapeo de nomenclatura
- [Modelos SQLAlchemy](../agm-simulated-enviroment/backend/app/models/entities.py) - Implementación de modelos
- [Esquemas Pydantic](../agm-simulated-enviroment/backend/app/models/schemas.py) - Esquemas de validación

