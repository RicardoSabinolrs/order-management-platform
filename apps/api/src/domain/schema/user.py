"""Contratos de usuarios."""

from __future__ import annotations

from pydantic import Field

from domain.model.user import EMAIL_PATTERN, Role, User
from domain.schema.base import BaseSchema


class UserCreate(BaseSchema):
    """Dados para um administrador cadastrar um usuario."""

    name: str = Field(min_length=1, max_length=120, examples=["Ana Souza"])
    email: str = Field(
        max_length=255, pattern=EMAIL_PATTERN.pattern, examples=["ana.souza@sabinolabs.dev"]
    )
    # Teto generoso so para que ninguem mande megabytes ao Argon2.
    password: str = Field(min_length=8, max_length=128)
    role: Role


class UserRead(BaseSchema):
    """Identidade de um usuario como a API a expoe. Nunca inclui o hash."""

    id: str
    name: str
    email: str
    role: Role
    avatar_url: str | None

    @classmethod
    def from_domain(cls, user: User) -> UserRead:
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatar_url=user.avatar_url,
        )
