"""Base dos schemas.

Schemas sao o contrato de entrada e saida dos services. Os endpoints apenas os
repassam: quem monta e quem consome sao os services.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Configuracao comum a todos os schemas."""

    model_config = ConfigDict(
        # Rejeita campo desconhecido na entrada: erro de digitacao em payload
        # vira 422 em vez de ser silenciosamente ignorado.
        extra="forbid",
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )
