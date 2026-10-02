"""A fronteira HTTP: serializacao, status e traducao de erros.

Os services sao ligados a repositorios em memoria, entao estes testes cobrem a
rota de verdade - roteamento, schema de entrada, corpo de saida e o mapeamento
de erro de dominio para codigo HTTP - sem precisar de banco.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.deps import get_unit_of_work_factory
from tests.fakes.unit_of_work import InMemoryDatabase

PRODUTO = {
    "sku": "CAF-500",
    "name": "Cafe torrado e moido 500g",
    "description": "Pacote de 500g",
    "price_in_cents": 3290,
    "initial_stock": 10,
}
CLIENTE = {"name": "Marina Duarte", "email": "marina@exemplo.com"}


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
async def api(app: FastAPI, database: InMemoryDatabase) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_unit_of_work_factory] = lambda: database
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client
    app.dependency_overrides.clear()


async def criar_produto(api: AsyncClient, **overrides: object) -> dict:
    response = await api.post("/products", json={**PRODUTO, **overrides})
    assert response.status_code == HTTPStatus.CREATED, response.text
    return response.json()


async def criar_pedido(api: AsyncClient, product_id: str, quantity: int = 2) -> dict:
    response = await api.post(
        "/orders",
        json={"customer": CLIENTE, "items": [{"product_id": product_id, "quantity": quantity}]},
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return response.json()


# -- produtos ---------------------------------------------------------------
async def test_cadastro_de_produto_devolve_201(api: AsyncClient) -> None:
    created = await criar_produto(api)

    assert created["sku"] == "CAF-500"
    assert created["active"] is True
    assert created["currency"] == "BRL"


async def test_sku_duplicado_devolve_409_problem_json(api: AsyncClient) -> None:
    await criar_produto(api)

    response = await api.post("/products", json=PRODUTO)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "duplicate_sku"


async def test_payload_invalido_devolve_422(api: AsyncClient) -> None:
    response = await api.post("/products", json={**PRODUTO, "price_in_cents": -5})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


async def test_campo_desconhecido_e_recusado(api: AsyncClient) -> None:
    # `extra="forbid"`: erro de digitacao no payload nao passa silenciosamente.
    response = await api.post("/products", json={**PRODUTO, "preco": 100})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_listagem_paginada_de_produtos(api: AsyncClient) -> None:
    for index in range(3):
        await criar_produto(api, sku=f"SKU-{index:03d}")

    response = await api.get("/products", params={"page": 1, "page_size": 2})

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body["items"]) == 2
    assert body["total"] == 3


async def test_alteracao_parcial_de_produto(api: AsyncClient) -> None:
    created = await criar_produto(api)

    response = await api.patch(f"/products/{created['id']}", json={"price_in_cents": 3990})

    assert response.status_code == HTTPStatus.OK
    assert response.json()["price_in_cents"] == 3990
    assert response.json()["name"] == created["name"]


async def test_exclusao_de_produto_devolve_204(api: AsyncClient) -> None:
    created = await criar_produto(api)

    response = await api.delete(f"/products/{created['id']}")

    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_produto_inexistente_devolve_404(api: AsyncClient) -> None:
    response = await api.get(f"/products/{uuid4()}")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "entity_not_found"


# -- estoque ----------------------------------------------------------------
async def test_estoque_nasce_junto_com_o_produto(api: AsyncClient) -> None:
    created = await criar_produto(api)

    response = await api.get(f"/stock/{created['id']}")

    body = response.json()
    assert body["quantity_on_hand"] == 10
    assert body["quantity_available"] == 10


async def test_entrada_de_mercadoria(api: AsyncClient) -> None:
    created = await criar_produto(api)

    response = await api.post(f"/stock/{created['id']}/receipts", json={"quantity": 5})

    assert response.json()["quantity_on_hand"] == 15


async def test_ajuste_de_inventario(api: AsyncClient) -> None:
    created = await criar_produto(api)

    response = await api.post(
        f"/stock/{created['id']}/adjustments",
        json={"quantity_on_hand": 8, "reason": "Inventario ciclico"},
    )

    assert response.json()["quantity_on_hand"] == 8


# -- pedidos ----------------------------------------------------------------
async def test_criacao_de_pedido_reserva_estoque(api: AsyncClient) -> None:
    product = await criar_produto(api)

    order = await criar_pedido(api, product["id"], quantity=4)

    assert order["status"] == "pending"
    assert order["total_in_cents"] == 4 * 3290

    stock = (await api.get(f"/stock/{product['id']}")).json()
    assert stock["quantity_reserved"] == 4
    assert stock["quantity_available"] == 6


async def test_estoque_insuficiente_devolve_409_com_detalhes(api: AsyncClient) -> None:
    product = await criar_produto(api, initial_stock=2)

    response = await api.post(
        "/orders",
        json={"customer": CLIENTE, "items": [{"product_id": product["id"], "quantity": 5}]},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    body = response.json()
    assert body["code"] == "insufficient_stock"
    # O corpo carrega o que o operador precisa para agir.
    assert body["requested"] == 5
    assert body["available"] == 2


async def test_ciclo_de_vida_completo_pela_api(api: AsyncClient) -> None:
    product = await criar_produto(api)
    order = await criar_pedido(api, product["id"], quantity=3)

    assert (await api.post(f"/orders/{order['id']}/confirm")).json()["status"] == "confirmed"
    assert (await api.post(f"/orders/{order['id']}/ship")).json()["status"] == "shipped"
    assert (await api.post(f"/orders/{order['id']}/deliver")).json()["status"] == "delivered"

    stock = (await api.get(f"/stock/{product['id']}")).json()
    assert stock["quantity_on_hand"] == 7
    assert stock["quantity_reserved"] == 0


async def test_transicao_invalida_devolve_409_com_as_opcoes(api: AsyncClient) -> None:
    product = await criar_produto(api)
    order = await criar_pedido(api, product["id"])

    response = await api.post(f"/orders/{order['id']}/deliver")

    assert response.status_code == HTTPStatus.CONFLICT
    body = response.json()
    assert body["code"] == "invalid_status_transition"
    assert body["allowed"] == ["cancelled", "confirmed"]


async def test_cancelamento_exige_motivo(api: AsyncClient) -> None:
    product = await criar_produto(api)
    order = await criar_pedido(api, product["id"])

    response = await api.post(f"/orders/{order['id']}/cancel", json={"reason": "x"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_cancelamento_libera_o_estoque(api: AsyncClient) -> None:
    product = await criar_produto(api)
    order = await criar_pedido(api, product["id"], quantity=4)

    response = await api.post(f"/orders/{order['id']}/cancel", json={"reason": "Cliente desistiu"})

    assert response.json()["status"] == "cancelled"
    stock = (await api.get(f"/stock/{product['id']}")).json()
    assert stock["quantity_available"] == 10


async def test_listagem_de_pedidos_filtra_por_status(api: AsyncClient) -> None:
    product = await criar_produto(api, initial_stock=50)
    primeiro = await criar_pedido(api, product["id"], quantity=1)
    await criar_pedido(api, product["id"], quantity=1)
    await api.post(f"/orders/{primeiro['id']}/confirm")

    response = await api.get("/orders", params={"status": "confirmed"})

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == primeiro["id"]


async def test_status_desconhecido_no_filtro_devolve_422(api: AsyncClient) -> None:
    response = await api.get("/orders", params={"status": "inventado"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
