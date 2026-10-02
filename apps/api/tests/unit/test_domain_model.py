"""Contratos dos blocos de construcao do dominio."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from domain.model import AggregateRoot, DomainEvent, Entity


class Customer(Entity[str]):
    pass


class Supplier(Entity[str]):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ThingHappened(DomainEvent):
    detail: str


class Thing(AggregateRoot[str]):
    def do_something(self, detail: str) -> None:
        self.record_event(ThingHappened(detail=detail))


def test_entidades_sao_iguais_quando_tem_o_mesmo_id() -> None:
    entity_id = str(uuid4())
    assert Customer(entity_id) == Customer(entity_id)


def test_entidades_de_tipos_diferentes_nunca_sao_iguais() -> None:
    entity_id = str(uuid4())
    assert Customer(entity_id) != Supplier(entity_id)


def test_entidade_e_hashavel_por_identidade() -> None:
    entity_id = str(uuid4())
    assert len({Customer(entity_id), Customer(entity_id)}) == 1


def test_pull_events_devolve_e_limpa_os_eventos_pendentes() -> None:
    thing = Thing("thing-1")
    thing.do_something("primeiro")
    thing.do_something("segundo")

    events = thing.pull_events()

    assert [event.name for event in events] == ["ThingHappened", "ThingHappened"]
    assert thing.pull_events() == ()


def test_evento_carrega_identidade_e_instante_com_fuso() -> None:
    event = ThingHappened(detail="algo")

    assert event.event_id is not None
    assert event.occurred_at.tzinfo is not None
    assert event.name == "ThingHappened"


def test_bump_version_avanca_o_lock_otimista() -> None:
    thing = Thing("thing-1")
    assert thing.version == 0

    thing.bump_version()

    assert thing.version == 1
