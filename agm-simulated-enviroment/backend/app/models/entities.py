from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Integer,
    SmallInteger,
    String,
    Text,
    CHAR,
    TIMESTAMP,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Category(Base):
    """Modelo para la tabla HLP_CATEGORIAS (legacy)"""

    __tablename__ = "HLP_CATEGORIAS"

    codcategoria: Mapped[int] = mapped_column(
        Integer, name="CODCATEGORIA", primary_key=True, nullable=False
    )
    categoria: Mapped[str] = mapped_column(String(50), name="CATEGORIA", nullable=False)

    # Relación con requests
    requests: Mapped[list["Request"]] = relationship(
        "Request", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category(codcategoria={self.codcategoria}, categoria={self.categoria})>"


class Request(Base):
    """Modelo para la tabla HLP_PETICIONES (legacy)"""

    __tablename__ = "HLP_PETICIONES"

    codpeticiones: Mapped[int] = mapped_column(
        BigInteger, name="CODPETICIONES", primary_key=True, autoincrement=True, nullable=False
    )
    codcategoria: Mapped[int] = mapped_column(
        Integer, ForeignKey("HLP_CATEGORIAS.CODCATEGORIA"), name="CODCATEGORIA", nullable=False
    )
    codestado: Mapped[Optional[int]] = mapped_column(
        SmallInteger, name="CODESTADO", nullable=True, server_default=text("1")
    )
    codprioridad: Mapped[Optional[int]] = mapped_column(
        SmallInteger, name="CODPRIORIDAD", nullable=True, server_default=text("3")
    )
    codgravedad: Mapped[Optional[int]] = mapped_column(
        SmallInteger, name="CODGRAVEDAD", nullable=True, server_default=text("2")
    )
    codfrecuencia: Mapped[Optional[int]] = mapped_column(
        SmallInteger, name="CODFRECUENCIA", nullable=True, server_default=text("3")
    )
    ususolicita: Mapped[str] = mapped_column(String(25), name="USUSOLICITA", nullable=False)
    fesolicita: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        name="FESOLICITA",
        nullable=False,
        server_default=func.now(),
    )
    description: Mapped[str] = mapped_column(Text, name="DESCRIPTION", nullable=False)
    solucion: Mapped[Optional[str]] = mapped_column(Text, name="SOLUCION", nullable=True)
    fesolucion: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), name="FESOLUCION", nullable=True
    )
    codusolucion: Mapped[Optional[str]] = mapped_column(String(24), name="CODUSOLUCION", nullable=True)
    codgrupo: Mapped[Optional[int]] = mapped_column(
        Integer, name="CODGRUPO", nullable=True, server_default=text("4")
    )
    oportuna: Mapped[Optional[str]] = mapped_column(
        CHAR(1), name="OPORTUNA", nullable=True, server_default=text("'X'")
    )
    feccierre: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), name="FECCIERRE", nullable=True
    )
    codmotcierre: Mapped[Optional[int]] = mapped_column(
        Integer, name="CODMOTCIERRE", nullable=True, server_default=text("5")
    )
    ai_classification_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, name="AI_CLASSIFICATION_DATA", nullable=True
    )

    # Relación con category
    category: Mapped["Category"] = relationship(
        "Category", back_populates="requests"
    )

    def __repr__(self) -> str:
        return f"<Request(codpeticiones={self.codpeticiones}, codcategoria={self.codcategoria}, codestado={self.codestado})>"

