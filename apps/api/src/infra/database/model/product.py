"""Tabela de produtos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from infra.database.base import Base


class ProductTable(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price_in_cents >= 0", name="price_nao_negativo"),)

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(1000), default="")
    price_in_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Lock otimista: o UPDATE exige a versao lida, entao duas escritas
    # concorrentes nao se sobrescrevem em silencio.
    version: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
