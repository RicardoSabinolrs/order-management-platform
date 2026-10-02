"""A API completa contra o Postgres real, pela porta HTTP."""

from __future__ import annotations

from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from infra.config.settings import Settings
from main import create_app

pytestmark = pytest.mark.integration

PRODUTO = {
    "sku": "CAF-500",
    "name": "Cafe torrado e moido 500g",
    "description": "Pacote de 500g",
    "price_in_cents": 3290,
    "initial_stock": 10,
}
CLIENTE = {"name": "Marina Duarte", "email": "marina@exemplo.com"}


@pytest.fixture
async def api(settings: Settings, database) -> AsyncIterator[AsyncClient]:
    """Cliente apontado para a aplicacao real, com banco real."""
    app = create_app(settings)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            yield client


async def test_readiness_confirma_o_postgres(settings: Settings, database) -> None:
    app = create_app(settings)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["dependencies"] == [{"name": "postgres", "healthy": True}]


async def test_jornada_completa_pela_api(api: AsyncClient) -> None:
    created = await api.post("/products", json=PRODUTO)
    assert created.status_code == HTTPStatus.CREATED, created.text
    product_id = created.json()["id"]

    await api.post(f"/stock/{product_id}/receipts", json={"quantity": 5})
    saldo = (await api.get(f"/stock/{product_id}")).json()
    assert saldo["quantity_on_hand"] == 15

    order = await api.post(
        "/orders",
        json={"customer": CLIENTE, "items": [{"product_id": product_id, "quantity": 4}]},
    )
    assert order.status_code == HTTPStatus.CREATED, order.text
    order_id = order.json()["id"]

    assert (await api.get(f"/stock/{product_id}")).json()["quantity_available"] == 11

    await api.post(f"/orders/{order_id}/confirm")
    await api.post(f"/orders/{order_id}/ship")
    entregue = await api.post(f"/orders/{order_id}/deliver")

    assert entregue.json()["status"] == "delivered"
    saldo = (await api.get(f"/stock/{product_id}")).json()
    assert saldo["quantity_on_hand"] == 11
    assert saldo["quantity_reserved"] == 0


async def test_sku_duplicado_esbarra_no_indice_unico(api: AsyncClient) -> None:
    assert (await api.post("/products", json=PRODUTO)).status_code == HTTPStatus.CREATED

    response = await api.post("/products", json=PRODUTO)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "duplicate_sku"


async def test_estoque_insuficiente_pela_api(api: AsyncClient) -> None:
    created = await api.post("/products", json={**PRODUTO, "initial_stock": 1})
    product_id = created.json()["id"]

    response = await api.post(
        "/orders",
        json={"customer": CLIENTE, "items": [{"product_id": product_id, "quantity": 9}]},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["available"] == 1
