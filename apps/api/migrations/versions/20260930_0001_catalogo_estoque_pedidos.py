"""Cria catalogo, estoque e pedidos

Revision ID: 0001_catalogo
Revises:
Create Date: 2026-09-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_catalogo"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("price_in_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("price_in_cents >= 0", name="ck_products_price_nao_negativo"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_active", "products", ["active"])

    op.create_table(
        "stock_items",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # As invariantes do agregado tambem no banco: nem um script avulso
        # consegue deixar o saldo inconsistente.
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_stock_items_saldo_nao_negativo"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_stock_items_reserva_nao_negativa"),
        sa.CheckConstraint(
            "quantity_reserved <= quantity_on_hand", name="ck_stock_items_reserva_ate_o_saldo"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_stock_items_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id", name="pk_stock_items"),
    )
    op.create_index("ix_stock_items_sku", "stock_items", ["sku"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("customer_name", sa.String(length=180), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "placed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
    )
    op.create_index("ix_orders_reference", "orders", ["reference"], unique=True)
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_customer_name", "orders", ["customer_name"])
    op.create_index("ix_orders_placed_at", "orders", ["placed_at"])

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=180), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_in_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantidade_positiva"),
        sa.CheckConstraint("unit_price_in_cents >= 0", name="ck_order_items_preco_nao_negativo"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_order_items_order_id_orders",
            ondelete="CASCADE",
        ),
        # RESTRICT: produto ja vendido nao pode sumir do catalogo.
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_order_items_product_id_products",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("stock_items")
    op.drop_table("products")
