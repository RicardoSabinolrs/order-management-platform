"""Porta de persistencia dos pedidos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from domain.model.order import Order, OrderStatus


@dataclass(frozen=True, slots=True)
class OrderFilter:
    """Criterios de busca de pedidos."""

    status: OrderStatus | None = None
    search: str | None = None


@dataclass(frozen=True, slots=True)
class OrderStatistics:
    """Numeros agregados de pedidos, calculados pelo banco."""

    total: int
    by_status: dict[OrderStatus, int]
    revenue_in_cents: int


@dataclass(frozen=True, slots=True)
class DailyOrders:
    """Pedidos e faturamento de um dia."""

    day: date
    orders: int
    revenue_in_cents: int


class OrderRepository(Protocol):
    async def get(self, order_id: UUID) -> Order | None: ...

    async def get_by_reference(self, reference: str) -> Order | None: ...

    async def paginate(
        self, *, filters: OrderFilter, offset: int, limit: int
    ) -> tuple[list[Order], int]: ...

    async def statistics(self) -> OrderStatistics:
        """Contagens e faturamento agregados.

        Somar isso no Python exigiria carregar todos os pedidos na memoria; o
        banco faz em uma consulta.
        """
        ...

    async def daily_totals(self, *, days: int) -> list[DailyOrders]:
        """Agregado por dia dos ultimos `days` dias.

        Devolve so os dias que tiveram pedido; preencher os vazios e trabalho
        do service, que conhece a janela pedida.
        """
        ...

    async def recent(self, limit: int) -> list[Order]:
        """Ultimos pedidos criados."""
        ...

    async def next_reference(self) -> str:
        """Gera a proxima referencia legivel (PED-000123)."""
        ...

    async def add(self, order: Order) -> None: ...

    async def save(self, order: Order) -> None: ...

    async def delete(self, order: Order) -> None: ...
