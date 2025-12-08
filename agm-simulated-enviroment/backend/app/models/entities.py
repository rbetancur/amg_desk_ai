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
        Integer, primary_key=True, nullable=False
    )
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)

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
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    codcategoria: Mapped[int] = mapped_column(
        Integer, ForeignKey("HLP_CATEGORIAS.CODCATEGORIA"), nullable=False
    )
    codestado: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, server_default=text("1")
    )
    codprioridad: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, server_default=text("3")
    )
    codgravedad: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, server_default=text("2")
    )
    codfrecuencia: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, server_default=text("3")
    )
    ususolicita: Mapped[str] = mapped_column(String(25), nullable=False)
    fesolicita: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    solucion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fesolucion: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    codusolucion: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    codgrupo: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, server_default=text("4")
    )
    oportuna: Mapped[Optional[str]] = mapped_column(
        CHAR(1), nullable=True, server_default=text("'X'")
    )
    feccierre: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    codmotcierre: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, server_default=text("5")
    )
    ai_classification_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )

    # Relación con category
    category: Mapped["Category"] = relationship(
        "Category", back_populates="requests"
    )

    def __repr__(self) -> str:
        return f"<Request(codpeticiones={self.codpeticiones}, codcategoria={self.codcategoria}, codestado={self.codestado})>"

