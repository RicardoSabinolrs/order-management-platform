"""Contratos de pedidos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from domain.model.order import Order, OrderItem, OrderStatus
from domain.schema.base import BaseSchema


class CustomerInput(BaseSchema):
    name: str = Field(min_length=1, max_length=180, examples=["Marina Duarte"])
    email: str = Field(examples=["marina.duarte@exemplo.com"])


class OrderItemInput(BaseSchema):
    """Item pedido. O preco vem do catalogo, nao do cliente."""

    product_id: UUID
    quantity: int = Field(gt=0, examples=[2])


class OrderCreate(BaseSchema):
    customer: CustomerInput
    items: list[OrderItemInput] = Field(min_length=1)


class OrderUpdate(BaseSchema):
    """Alteracao de um pedido ainda pendente."""

    customer: CustomerInput | None = None
    items: list[OrderItemInput] | None = Field(default=None, min_length=1)


class OrderCancel(BaseSchema):
    reason: str = Field(min_length=3, max_length=280, examples=["Cliente desistiu da compra"])


class OrderItemRead(BaseSchema):
    product_id: UUID
    sku: str
    description: str
    quantity: int
    unit_price_in_cents: int
    subtotal_in_cents: int

    @classmethod
    def from_domain(cls, item: OrderItem) -> OrderItemRead:
        return cls(
            product_id=item.product_id,
            sku=item.sku,
            description=item.description,
            quantity=item.quantity,
            unit_price_in_cents=item.unit_price.amount_in_cents,
            subtotal_in_cents=item.subtotal.amount_in_cents,
        )


class CustomerRead(BaseSchema):
    name: str
    email: str


class OrderRead(BaseSchema):
    """Pedido completo, com as linhas."""

    id: UUID
    reference: str
    status: OrderStatus
    customer: CustomerRead
    items: list[OrderItemRead]
    total_in_cents: int
    currency: str
    cancellation_reason: str | None
    placed_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> OrderRead:
        return cls(
            id=order.id,
            reference=order.reference,
            status=order.status,
            customer=CustomerRead(name=order.customer.name, email=order.customer.email),
            items=[OrderItemRead.from_domain(item) for item in order.items],
            total_in_cents=order.total.amount_in_cents,
            currency=order.total.currency,
            cancellation_reason=order.cancellation_reason,
            placed_at=order.placed_at,
            updated_at=order.updated_at,
        )


class OrderSummary(BaseSchema):
    """Versao enxuta usada na listagem: sem as linhas do pedido."""

    id: UUID
    reference: str
    status: OrderStatus
    customer_name: str
    item_count: int
    total_in_cents: int
    placed_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> OrderSummary:
        return cls(
            id=order.id,
            reference=order.reference,
            status=order.status,
            customer_name=order.customer.name,
            item_count=order.item_count,
            total_in_cents=order.total.amount_in_cents,
            placed_at=order.placed_at,
        )
