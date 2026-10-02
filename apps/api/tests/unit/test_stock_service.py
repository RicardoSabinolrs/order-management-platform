"""StockService com repositorios em memoria."""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.exception import BusinessRuleViolationError, EntityNotFoundError
from domain.schema.page import PageQuery
from domain.schema.product import ProductCreate
from domain.schema.stock import StockAdjust, StockReceive
from domain.service.product import ProductService
from domain.service.stock import StockService
from tests.fakes.unit_of_work import InMemoryDatabase


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def stock_service(database: InMemoryDatabase) -> StockService:
    return StockService(database)


@pytest.fixture
def product_service(database: InMemoryDatabase) -> ProductService:
    return ProductService(database)


async def criar_produto(service: ProductService, *, initial_stock: int = 0):
    return await service.create(
        ProductCreate(
            sku="CAF-500",
            name="Cafe 500g",
            description="",
            price_in_cents=3290,
            initial_stock=initial_stock,
        )
    )


async def test_entrada_soma_ao_saldo(
    product_service: ProductService, stock_service: StockService
) -> None:
    product = await criar_produto(product_service, initial_stock=10)

    result = await stock_service.receive(product.id, StockReceive(quantity=15))

    assert result.quantity_on_hand == 25
    assert result.quantity_available == 25


async def test_ajuste_corrige_o_saldo(
    product_service: ProductService, stock_service: StockService
) -> None:
    product = await criar_produto(product_service, initial_stock=10)

    result = await stock_service.adjust(
        product.id, StockAdjust(quantity_on_hand=7, reason="Inventario ciclico")
    )

    assert result.quantity_on_hand == 7


async def test_ajuste_abaixo_do_reservado_e_recusado(
    product_service: ProductService,
    stock_service: StockService,
    database: InMemoryDatabase,
) -> None:
    product = await criar_produto(product_service, initial_stock=10)
    database.stock[product.id].reserve(6)

    with pytest.raises(BusinessRuleViolationError, match="reservada"):
        await stock_service.adjust(
            product.id, StockAdjust(quantity_on_hand=3, reason="Quebra no deposito")
        )


async def test_listagem_pagina_os_saldos(
    product_service: ProductService, stock_service: StockService, database: InMemoryDatabase
) -> None:
    for index in range(3):
        await product_service.create(
            ProductCreate(
                sku=f"SKU-{index:03d}",
                name=f"Produto {index}",
                description="",
                price_in_cents=1000,
                initial_stock=index,
            )
        )

    page = await stock_service.paginate(page_query=PageQuery(page=1, page_size=2))

    assert len(page.items) == 2
    assert page.total == 3


async def test_estoque_de_produto_inexistente(stock_service: StockService) -> None:
    with pytest.raises(EntityNotFoundError, match="registro de estoque"):
        await stock_service.get(uuid4())
