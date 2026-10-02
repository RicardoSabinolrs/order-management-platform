"""Contratos do catalogo de produtos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from domain.model.product import Product
from domain.schema.base import BaseSchema


class ProductCreate(BaseSchema):
    """Dados para cadastrar um produto."""

    sku: str = Field(min_length=3, max_length=32, examples=["CAF-500"])
    name: str = Field(min_length=1, max_length=120, examples=["Cafe torrado e moido 500g"])
    description: str = Field(default="", max_length=1000)
    price_in_cents: int = Field(ge=0, examples=[3290])
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    # Estoque inicial e opcional: o produto pode ser cadastrado antes de chegar.
    initial_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseSchema):
    """Alteracao parcial: somente os campos enviados mudam."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price_in_cents: int | None = Field(default=None, ge=0)
    active: bool | None = None


class ProductRead(BaseSchema):
    """Produto como a API o expoe."""

    id: UUID
    sku: str
    name: str
    description: str
    price_in_cents: int
    currency: str
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, product: Product) -> ProductRead:
        return cls(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            price_in_cents=product.price.amount_in_cents,
            currency=product.price.currency,
            active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
