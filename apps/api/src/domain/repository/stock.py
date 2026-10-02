"""Porta de persistencia do estoque."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from domain.model.stock import StockItem


@dataclass(frozen=True, slots=True)
class StockOverview:
    """Numeros agregados de estoque."""

    units_on_hand: int
    units_reserved: int
    out_of_stock: int


class StockRepository(Protocol):
    async def get(self, product_id: UUID) -> StockItem | None: ...

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, StockItem]: ...

    async def get_for_update(self, product_id: UUID) -> StockItem | None:
        """Carrega o saldo travando a linha ate o fim da transacao.

        Reserva e uma operacao ler-decidir-escrever: sem o lock, dois pedidos
        simultaneos leem o mesmo saldo e vendem a mesma unidade duas vezes.
        """
        ...

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[StockItem], int]: ...

    async def overview(self) -> StockOverview:
        """Totais de saldo e quantos produtos zeraram o disponivel."""
        ...

    async def low_stock(self, *, threshold: int, limit: int) -> list[StockItem]:
        """Produtos com disponivel menor ou igual ao limite, do menor ao maior."""
        ...

    async def add(self, stock: StockItem) -> None: ...

    async def save(self, stock: StockItem) -> None: ...
