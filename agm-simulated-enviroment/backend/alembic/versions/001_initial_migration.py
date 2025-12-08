"""Initial migration: Create HLP_CATEGORIAS and HLP_PETICIONES tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-08 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla HLP_CATEGORIAS
    op.create_table(
        "HLP_CATEGORIAS",
        sa.Column("CODCATEGORIA", sa.Integer(), nullable=False),
        sa.Column("CATEGORIA", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("CODCATEGORIA"),
    )

    # Crear tabla HLP_PETICIONES
    op.create_table(
        "HLP_PETICIONES",
        sa.Column("CODPETICIONES", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("CODCATEGORIA", sa.Integer(), nullable=False),
        sa.Column("CODESTADO", sa.SmallInteger(), nullable=True, server_default=text("1")),
        sa.Column("CODPRIORIDAD", sa.SmallInteger(), nullable=True, server_default=text("3")),
        sa.Column("CODGRAVEDAD", sa.SmallInteger(), nullable=True, server_default=text("2")),
        sa.Column("CODFRECUENCIA", sa.SmallInteger(), nullable=True, server_default=text("3")),
        sa.Column("USUSOLICITA", sa.String(length=25), nullable=False),
        sa.Column("FESOLICITA", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("DESCRIPTION", sa.Text(), nullable=False),
        sa.Column("SOLUCION", sa.Text(), nullable=True),
        sa.Column("FESOLUCION", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("CODUSOLUCION", sa.String(length=24), nullable=True),
        sa.Column("CODGRUPO", sa.Integer(), nullable=True, server_default=text("4")),
        sa.Column("OPORTUNA", sa.CHAR(length=1), nullable=True, server_default=text("'X'")),
        sa.Column("FECCIERRE", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("CODMOTCIERRE", sa.Integer(), nullable=True, server_default=text("5")),
        sa.Column("AI_CLASSIFICATION_DATA", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["CODCATEGORIA"],
            ["HLP_CATEGORIAS.CODCATEGORIA"],
        ),
        sa.PrimaryKeyConstraint("CODPETICIONES"),
    )

    # Crear índices para campos de búsqueda frecuente
    op.create_index(
        op.f("ix_HLP_PETICIONES_CODCATEGORIA"),
        "HLP_PETICIONES",
        ["CODCATEGORIA"],
        unique=False,
    )
    op.create_index(
        op.f("ix_HLP_PETICIONES_CODESTADO"),
        "HLP_PETICIONES",
        ["CODESTADO"],
        unique=False,
    )
    op.create_index(
        op.f("ix_HLP_PETICIONES_USUSOLICITA"),
        "HLP_PETICIONES",
        ["USUSOLICITA"],
        unique=False,
    )
    op.create_index(
        op.f("ix_HLP_PETICIONES_FESOLICITA"),
        "HLP_PETICIONES",
        ["FESOLICITA"],
        unique=False,
    )

    # Insertar datos seed para HLP_CATEGORIAS
    op.execute(
        text("""
        INSERT INTO "HLP_CATEGORIAS" ("CODCATEGORIA", "CATEGORIA") VALUES
        (300, 'Cambio de Contraseña Cuenta Dominio'),
        (400, 'Cambio de Contraseña Amerika')
        ON CONFLICT ("CODCATEGORIA") DO NOTHING;
        """)
    )


def downgrade() -> None:
    # Eliminar índices
    op.drop_index(op.f("ix_HLP_PETICIONES_FESOLICITA"), table_name="HLP_PETICIONES")
    op.drop_index(op.f("ix_HLP_PETICIONES_USUSOLICITA"), table_name="HLP_PETICIONES")
    op.drop_index(op.f("ix_HLP_PETICIONES_CODESTADO"), table_name="HLP_PETICIONES")
    op.drop_index(op.f("ix_HLP_PETICIONES_CODCATEGORIA"), table_name="HLP_PETICIONES")

    # Eliminar tablas
    op.drop_table("HLP_PETICIONES")
    op.drop_table("HLP_CATEGORIAS")

