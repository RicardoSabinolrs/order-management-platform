"""Eventos de dominio.

Fatos imutaveis, nomeados no passado (OrderPlaced, OrderShipped). Os modelos
apenas os registram; publicar e responsabilidade do service, depois do commit -
um evento anuncia algo consumado, nao algo que ainda pode falhar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Fato consumado dentro do dominio."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def name(self) -> str:
        """Nome estavel do evento, usado em logs e no barramento."""
        return type(self).__name__
