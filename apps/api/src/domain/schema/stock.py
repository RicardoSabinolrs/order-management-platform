"""Contratos de estoque."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from domain.model.stock import StockItem
from domain.schema.base import BaseSchema


class StockReceive(BaseSchema):
    """Entrada de mercadoria."""

    quantity: int = Field(gt=0, examples=[50])


class StockAdjust(BaseSchema):
    """Correcao de saldo apos inventario."""

    quantity_on_hand: int = Field(ge=0, examples=[48])
    reason: str = Field(min_length=3, max_length=280, examples=["Inventario ciclico de outubro"])


class StockRead(BaseSchema):
    """Saldo como a API o expoe."""

    product_id: UUID
    sku: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    updated_at: datetime

    @classmethod
    def from_domain(cls, stock: StockItem) -> StockRead:
        return cls(
            product_id=stock.product_id,
            sku=stock.sku,
            quantity_on_hand=stock.quantity_on_hand,
            quantity_reserved=stock.quantity_reserved,
            quantity_available=stock.quantity_available,
            updated_at=stock.updated_at,
        )
