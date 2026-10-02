"""Fluxo de pedido fim a fim contra o Postgres real."""

from __future__ import annotations

import asyncio

import pytest

from domain.model.order import OrderStatus
from domain.model.stock import InsufficientStockError
from domain.schema.order import CustomerInput, OrderCancel, OrderCreate, OrderItemInput
from domain.schema.page import PageQuery
from domain.schema.product import ProductCreate
from domain.service.order import OrderService
from domain.service.product import ProductService
from domain.service.stock import StockService

pytestmark = pytest.mark.integration

CLIENTE = CustomerInput(name="Marina Duarte", email="marina@exemplo.com")


@pytest.fixture
def products(unit_of_work_factory) -> ProductService:
    return ProductService(unit_of_work_factory)


@pytest.fixture
def stock(unit_of_work_factory) -> StockService:
    return StockService(unit_of_work_factory)


@pytest.fixture
def orders(unit_of_work_factory) -> OrderService:
    return OrderService(unit_of_work_factory)


async def novo_produto(service: ProductService, *, sku: str = "CAF-500", stock_inicial: int = 10):
    return await service.create(
        ProductCreate(
            sku=sku,
            name="Cafe torrado e moido 500g",
            description="Pacote de 500g",
            price_in_cents=3290,
            initial_stock=stock_inicial,
        )
    )


async def test_fluxo_completo_persiste_cada_etapa(
    products: ProductService, stock: StockService, orders: OrderService
) -> None:
    product = await novo_produto(products, stock_inicial=10)

    order = await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=3)])
    )
    saldo = await stock.get(product.id)
    assert saldo.quantity_reserved == 3
    assert saldo.quantity_on_hand == 10

    await orders.confirm(order.id)
    await orders.ship(order.id)

    saldo = await stock.get(product.id)
    assert saldo.quantity_on_hand == 7
    assert saldo.quantity_reserved == 0

    final = await orders.deliver(order.id)
    assert final.status is OrderStatus.DELIVERED


async def test_cancelamento_devolve_o_saldo_no_banco(
    products: ProductService, stock: StockService, orders: OrderService
) -> None:
    product = await novo_produto(products, stock_inicial=10)
    order = await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=6)])
    )

    await orders.cancel(order.id, OrderCancel(reason="Cliente desistiu"))

    saldo = await stock.get(product.id)
    assert saldo.quantity_reserved == 0
    assert saldo.quantity_available == 10


async def test_falha_de_estoque_nao_deixa_pedido_orfao(
    products: ProductService, stock: StockService, orders: OrderService
) -> None:
    """A transacao inteira e desfeita: nem pedido, nem reserva parcial."""
    product = await novo_produto(products, stock_inicial=2)

    with pytest.raises(InsufficientStockError):
        await orders.create(
            OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=5)])
        )

    page = await orders.paginate(page_query=PageQuery())
    assert page.total == 0

    saldo = await stock.get(product.id)
    assert saldo.quantity_reserved == 0


async def test_falha_no_segundo_item_desfaz_a_reserva_do_primeiro(
    products: ProductService, stock: StockService, orders: OrderService
) -> None:
    com_saldo = await novo_produto(products, sku="CAF-500", stock_inicial=10)
    sem_saldo = await novo_produto(products, sku="CHA-100", stock_inicial=1)

    with pytest.raises(InsufficientStockError):
        await orders.create(
            OrderCreate(
                customer=CLIENTE,
                items=[
                    OrderItemInput(product_id=com_saldo.id, quantity=2),
                    OrderItemInput(product_id=sem_saldo.id, quantity=5),
                ],
            )
        )

    # O primeiro item chegou a ser reservado dentro da transacao; o rollback
    # precisa ter devolvido tudo.
    assert (await stock.get(com_saldo.id)).quantity_reserved == 0
    assert (await stock.get(sem_saldo.id)).quantity_reserved == 0


async def test_reservas_concorrentes_nao_vendem_a_mesma_unidade(
    products: ProductService, stock: StockService, orders: OrderService
) -> None:
    """O `SELECT ... FOR UPDATE` e o que sustenta esta garantia.

    Dois pedidos disputam as ultimas 5 unidades pedindo 3 cada. Sem o lock,
    ambos leriam "5 disponiveis" e reservariam 6 no total. Com ele, um passa e
    o outro e recusado.
    """
    product = await novo_produto(products, stock_inicial=5)

    def novo_pedido():
        return orders.create(
            OrderCreate(
                customer=CLIENTE,
                items=[OrderItemInput(product_id=product.id, quantity=3)],
            )
        )

    resultados = await asyncio.gather(novo_pedido(), novo_pedido(), return_exceptions=True)

    sucessos = [r for r in resultados if not isinstance(r, BaseException)]
    falhas = [r for r in resultados if isinstance(r, BaseException)]

    assert len(sucessos) == 1, "somente um pedido pode levar as unidades"
    assert len(falhas) == 1
    assert isinstance(falhas[0], InsufficientStockError)

    saldo = await stock.get(product.id)
    assert saldo.quantity_reserved == 3
    assert saldo.quantity_available == 2
