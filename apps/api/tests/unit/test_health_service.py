"""Logica do HealthService, testada sem HTTP e sem banco.

Esta e a razao de a regra morar no service: um duble em memoria basta.
"""

from __future__ import annotations

import pytest

from domain.exception import DependencyUnavailableError
from domain.service.health import HealthService


class FakeHealthRepository:
    def __init__(self, *, available: bool) -> None:
        self._available = available
        self.calls = 0

    async def is_available(self) -> bool:
        self.calls += 1
        return self._available


def build_service(*, available: bool) -> tuple[HealthService, FakeHealthRepository]:
    repository = FakeHealthRepository(available=available)
    service = HealthService(repository, service_name="api-de-teste", version="9.9.9")
    return service, repository


def test_liveness_nao_consulta_dependencia() -> None:
    service, repository = build_service(available=False)

    result = service.liveness()

    assert result.status == "alive"
    assert result.service == "api-de-teste"
    assert result.version == "9.9.9"
    # Liveness que consulta o banco faria o Kubernetes reiniciar pods saudaveis
    # sempre que o banco oscilasse.
    assert repository.calls == 0


async def test_readiness_lista_as_dependencias_quando_todas_respondem() -> None:
    service, _ = build_service(available=True)

    result = await service.readiness()

    assert result.status == "ready"
    assert [(d.name, d.healthy) for d in result.dependencies] == [("postgres", True)]


async def test_readiness_falha_quando_uma_dependencia_esta_fora() -> None:
    service, _ = build_service(available=False)

    with pytest.raises(DependencyUnavailableError) as exc_info:
        await service.readiness()

    error = exc_info.value
    assert error.code == "dependency_unavailable"
    assert error.details() == {"dependencies": [{"name": "postgres", "healthy": False}]}
