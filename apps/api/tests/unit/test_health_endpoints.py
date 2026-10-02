"""Sondas expostas ao Kubernetes.

O endpoint so repassa o service, entao o teste substitui o service inteiro.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.deps import get_health_service
from domain.service.health import HealthService


class FakeHealthRepository:
    def __init__(self, *, available: bool) -> None:
        self._available = available

    async def is_available(self) -> bool:
        return self._available


@pytest.fixture
def override_health(app: FastAPI):
    def _override(*, available: bool) -> None:
        app.dependency_overrides[get_health_service] = lambda: HealthService(
            FakeHealthRepository(available=available),
            service_name="api-de-teste",
            version="9.9.9",
        )

    return _override


async def client_for(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_liveness_responde_alive(app: FastAPI, override_health) -> None:
    override_health(available=True)

    async with await client_for(app) as client:
        response = await client.get("/health/live")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "alive", "service": "api-de-teste", "version": "9.9.9"}


async def test_readiness_responde_ready_quando_tudo_esta_no_ar(
    app: FastAPI, override_health
) -> None:
    override_health(available=True)

    async with await client_for(app) as client:
        response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "status": "ready",
        "dependencies": [{"name": "postgres", "healthy": True}],
    }


async def test_readiness_responde_503_com_problem_json_quando_degradado(
    app: FastAPI, override_health
) -> None:
    override_health(available=False)

    async with await client_for(app) as client:
        response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.headers["content-type"].startswith("application/problem+json")

    body = response.json()
    assert body["code"] == "dependency_unavailable"
    assert body["dependencies"] == [{"name": "postgres", "healthy": False}]


async def test_metricas_usam_a_rota_parametrizada(client: AsyncClient) -> None:
    await client.get("/health/live")

    response = await client.get("/metrics")

    assert response.status_code == HTTPStatus.OK
    assert 'path="/health/live"' in response.text


async def test_resposta_carrega_id_de_correlacao(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


async def test_rota_inexistente_devolve_problem_json(client: AsyncClient) -> None:
    response = await client.get("/nao-existe")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"].startswith("application/problem+json")
