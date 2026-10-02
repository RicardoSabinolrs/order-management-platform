"""Tabela de saldos de estoque."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from infra.database.base import Base


class StockItemTable(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        # As mesmas invariantes do agregado, tambem no banco: uma escrita fora
        # da aplicacao (script, correcao manual) nao pode corromper o saldo.
        CheckConstraint("quantity_on_hand >= 0", name="saldo_nao_negativo"),
        CheckConstraint("quantity_reserved >= 0", name="reserva_nao_negativa"),
        CheckConstraint("quantity_reserved <= quantity_on_hand", name="reserva_ate_o_saldo"),
    )

    product_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sku: Mapped[str] = mapped_column(String(32), index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
