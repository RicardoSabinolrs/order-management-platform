"""Contratos do painel de controle."""

from __future__ import annotations

from datetime import date

from pydantic import Field

from domain.model.order import OrderStatus
from domain.schema.base import BaseSchema
from domain.schema.order import OrderSummary


class StatusCount(BaseSchema):
    status: OrderStatus
    count: int


class DailyPoint(BaseSchema):
    """Um ponto da serie diaria."""

    date: date
    orders: int
    revenue_in_cents: int


class LowStockItem(BaseSchema):
    """Produto perto de acabar."""

    product_id: str
    sku: str
    quantity_available: int
    quantity_reserved: int


class DashboardRead(BaseSchema):
    """Visao consolidada de pedidos e estoque."""

    orders_total: int
    orders_open: int = Field(description="Pedidos pendentes ou confirmados.")
    orders_by_status: list[StatusCount]

    revenue_in_cents: int = Field(description="Soma dos pedidos nao cancelados.")
    average_ticket_in_cents: int

    products_total: int
    products_active: int

    units_on_hand: int
    units_reserved: int
    out_of_stock: int = Field(description="Produtos com disponivel igual a zero.")
    low_stock: list[LowStockItem]

    daily: list[DailyPoint] = Field(
        description="Serie continua dos ultimos dias, com zeros nos dias sem pedido."
    )

    recent_orders: list[OrderSummary]
