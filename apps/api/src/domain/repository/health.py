"""Contrato de verificacao de saude das dependencias."""

from __future__ import annotations

from typing import Protocol


class HealthRepository(Protocol):
    """Responde se o armazenamento esta acessivel."""

    async def is_available(self) -> bool:
        """`True` se a dependencia responde; nunca levanta excecao."""
        ...
