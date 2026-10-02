"""Contratos de persistencia.

O dominio declara o que precisa; `infra/repository` implementa. Por isso os
services podem ser testados com dubles em memoria, sem banco nenhum.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from domain.repository.order import OrderRepository
from domain.repository.product import ProductRepository
from domain.repository.stock import StockRepository
from domain.repository.user import UserRepository


class UnitOfWork(Protocol):
    """Transacao em torno de uma operacao de negocio.

    Expoe os repositorios da mesma transacao: criar um pedido grava o pedido e
    reserva o estoque juntos, ou nao grava nada.
    """

    @property
    def products(self) -> ProductRepository: ...

    @property
    def stock(self) -> StockRepository: ...

    @property
    def orders(self) -> OrderRepository: ...

    @property
    def users(self) -> UserRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
