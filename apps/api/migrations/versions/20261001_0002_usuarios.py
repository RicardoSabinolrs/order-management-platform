"""Cria a tabela de usuarios

Revision ID: 0002_usuarios
Revises: 0001_catalogo
Create Date: 2026-10-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_usuarios"
down_revision: str | None = "0001_catalogo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # O indice unico so vale se o e-mail entrar sempre minusculo.
        # `op.f` marca o nome como final: sem ele a naming convention do
        # metadata prefixaria "ck_users_" uma segunda vez.
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_minusculo")),
        sa.CheckConstraint(
            "role IN ('admin', 'operator', 'viewer')", name=op.f("ck_users_role_valido")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
