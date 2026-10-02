"""Unidade de trabalho sobre uma sessao do SQLAlchemy."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.repository.user import UserRepository
from infra.repository.order import SqlAlchemyOrderRepository
from infra.repository.product import SqlAlchemyProductRepository
from infra.repository.stock import SqlAlchemyStockRepository
from infra.repository.user import (
    CompositeUserRepository,
    SettingsUserRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork:
    """Implementa a porta `UnitOfWork`.

    Os repositorios compartilham a mesma sessao, logo a mesma transacao:
    gravar o pedido e reservar o estoque e uma operacao so. Sem `commit`
    explicito, sair do contexto descarta tudo - nada e gravado por acidente.

    Com `root_users`, `users` enxerga tambem o administrador da configuracao;
    sem ele (testes de repositorio, scripts), so a tabela.
    """

    products: SqlAlchemyProductRepository
    stock: SqlAlchemyStockRepository
    orders: SqlAlchemyOrderRepository
    users: UserRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        root_users: SettingsUserRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._root_users = root_users
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            msg = "A unidade de trabalho precisa ser usada dentro de 'async with'."
            raise RuntimeError(msg)
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.products = SqlAlchemyProductRepository(self._session)
        self.stock = SqlAlchemyStockRepository(self._session)
        self.orders = SqlAlchemyOrderRepository(self._session)
        stored_users = SqlAlchemyUserRepository(self._session)
        self.users = (
            stored_users
            if self._root_users is None
            else CompositeUserRepository(self._root_users, stored_users)
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
