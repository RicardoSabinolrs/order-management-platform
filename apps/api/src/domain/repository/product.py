"""Porta de persistencia do catalogo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from domain.model.product import Product


@dataclass(frozen=True, slots=True)
class ProductFilter:
    """Criterios de busca do catalogo."""

    search: str | None = None
    active: bool | None = None


class ProductRepository(Protocol):
    async def get(self, product_id: UUID) -> Product | None: ...

    async def get_by_sku(self, sku: str) -> Product | None: ...

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, Product]:
        """Carrega varios produtos de uma vez.

        Existe para evitar o N+1 ao montar um pedido com muitas linhas.
        """
        ...

    async def paginate(
        self, *, filters: ProductFilter, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        """Pagina de produtos e o total que satisfaz o filtro."""
        ...

    async def counts(self) -> tuple[int, int]:
        """Total de produtos e quantos estao ativos."""
        ...

    async def add(self, product: Product) -> None: ...

    async def save(self, product: Product) -> None: ...

    async def delete(self, product: Product) -> None: ...
