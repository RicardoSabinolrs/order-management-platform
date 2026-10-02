"""Tabela de usuarios."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from infra.database.base import Base


class UserTable(Base):
    __tablename__ = "users"
    __table_args__ = (
        # O indice unico so protege contra duplicata se todo e-mail entrar
        # normalizado: o banco recusa a variante maiuscula que escapar do dominio.
        CheckConstraint("email = lower(email)", name="email_minusculo"),
        CheckConstraint("role IN ('admin', 'operator', 'viewer')", name="role_valido"),
    )

    # Texto, nao UUID nativo: o id do usuario e o `sub` do token, e o admin da
    # configuracao tem um id que nao e UUID.
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
