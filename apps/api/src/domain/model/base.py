"""Blocos de construcao dos modelos de dominio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from domain.model.event import DomainEvent


@dataclass(frozen=True, slots=True)
class ValueObject:
    """Objeto sem identidade, imutavel e com igualdade estrutural.

    Subclasses validam suas invariantes em `__post_init__` e lancam
    `InvariantViolationError`.
    """


class Entity[IdT]:
    """Objeto com identidade estavel ao longo do ciclo de vida.

    Duas entidades sao iguais quando tem o mesmo tipo e o mesmo id, ainda que
    os demais atributos divirjam.
    """

    __slots__ = ("_id",)

    def __init__(self, entity_id: IdT) -> None:
        self._id = entity_id

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)) or not isinstance(self, type(other)):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._id))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r})"


class AggregateRoot[IdT](Entity[IdT]):
    """Fronteira de consistencia transacional.

    Toda escrita entra pela raiz, que mantem as invariantes e registra os
    eventos resultantes. `version` sustenta o lock otimista no repositorio.
    """

    __slots__ = ("_events", "_version")

    def __init__(self, entity_id: IdT, *, version: int = 0) -> None:
        super().__init__(entity_id)
        self._version = version
        self._events: list[DomainEvent] = []

    @property
    def version(self) -> int:
        return self._version

    def record_event(self, event: DomainEvent) -> None:
        """Registra um fato ocorrido dentro da fronteira do agregado."""
        self._events.append(event)

    def pull_events(self) -> tuple[DomainEvent, ...]:
        """Devolve e limpa os eventos pendentes (consumido pelo service)."""
        events = tuple(self._events)
        self._events.clear()
        return events

    def bump_version(self) -> Self:
        """Avanca a versao apos uma escrita confirmada."""
        self._version += 1
        return self
