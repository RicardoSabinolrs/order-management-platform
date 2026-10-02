"""Base declarativa dos modelos de persistencia."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nomes deterministicos para constraints. Sem isso o autogenerate do Alembic
# produz migrations instaveis e drops anonimos.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base de todas as tabelas.

    Tabela e modelo de dominio sao coisas distintas: esta classe descreve o
    schema relacional, nao as regras de negocio.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
