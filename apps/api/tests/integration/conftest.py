"""Infraestrutura dos testes de integracao.

Exigem Postgres no ar (`make up` ou `make db-up`). O schema e criado a partir
do metadata e as tabelas sao limpas entre os testes, para que cada um comece de
um estado conhecido sem pagar o custo de recriar o banco.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text

from infra.config.settings import Settings
from infra.database.base import Base
from infra.database.session import Database
from infra.database.unit_of_work import SqlAlchemyUnitOfWork

# Importa os modelos para registrar as tabelas no metadata.
from infra.database import model  # noqa: F401  isort: skip

TABLES = ("order_items", "orders", "stock_items", "products", "users")


@pytest.fixture(scope="session")
async def database(settings: Settings) -> AsyncIterator[Database]:
    db = Database(settings.database)

    async with db.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield db
    finally:
        await db.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(database: Database) -> AsyncIterator[None]:
    """Zera as tabelas antes de cada teste.

    TRUNCATE CASCADE em vez de DROP/CREATE: milissegundos em vez de segundos,
    e o mesmo isolamento.
    """
    async with database.engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
    yield


@pytest.fixture
def unit_of_work_factory(database: Database):
    """Fabrica de transacoes reais, para injetar nos services."""
    return lambda: SqlAlchemyUnitOfWork(database.session_factory)
