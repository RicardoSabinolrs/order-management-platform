"""Tabelas de pedidos e suas linhas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.database.base import Base


class OrderTable(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    reference: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)

    customer_name: Mapped[str] = mapped_column(String(180), index=True)
    customer_email: Mapped[str] = mapped_column(String(255))

    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    cancellation_reason: Mapped[str | None] = mapped_column(Text, default=None)
    version: Mapped[int] = mapped_column(Integer, default=0)

    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # As linhas pertencem ao pedido e nao existem fora dele: cascade total e
    # carga junto com a raiz, porque o agregado so faz sentido completo.
    items: Mapped[list[OrderItemTable]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItemTable.position",
    )


class OrderItemTable(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantidade_positiva"),
        CheckConstraint("unit_price_in_cents >= 0", name="preco_nao_negativo"),
    )

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    order_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    # RESTRICT: um produto vendido nao pode ser apagado do catalogo.
    product_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT")
    )

    position: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(180))
    quantity: Mapped[int] = mapped_column(Integer)
    # Preco praticado na venda, copiado do catalogo: mudanca de tabela depois
    # nao reescreve o historico.
    unit_price_in_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")

    order: Mapped[OrderTable] = relationship(back_populates="items")
