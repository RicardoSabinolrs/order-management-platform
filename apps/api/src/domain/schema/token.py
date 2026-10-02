"""Schemas de autenticacao."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from domain.schema.base import BaseSchema


class TokenSchema(BaseSchema):
    """Par token/tipo devolvido no login."""

    access_token: str
    # "bearer" e o nome do esquema de autenticacao (RFC 6750), nao um segredo.
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int = Field(description="Validade do token, em segundos.")


class TokenPayloadSchema(BaseSchema):
    """Claims do access token, ja validadas."""

    sub: str = Field(description="Identificador do dono do token.")
    iss: str = Field(description="Emissor que assinou o token.")
    exp: datetime
    iat: datetime
    scopes: list[str] = Field(default_factory=list)
