"""Contratos de autenticacao."""

from __future__ import annotations

from pydantic import Field

from domain.schema.base import BaseSchema
from domain.schema.token import TokenSchema
from domain.schema.user import UserRead


class LoginRequest(BaseSchema):
    email: str = Field(examples=["operador@sabinolabs.dev"])
    password: str = Field(min_length=1)


class LoginResponse(TokenSchema):
    """Token emitido no login, acompanhado do usuario autenticado."""

    user: UserRead
