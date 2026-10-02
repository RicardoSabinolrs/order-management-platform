"""OrderService: a interacao entre pedido e estoque.

Estes testes sao o nucleo da suite. Eles descrevem a regra que o projeto
existe para sustentar: um pedido so nasce se houver saldo, e todo movimento do
pedido tem um efeito correspondente no estoque.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.exception import BusinessRuleViolationError, EntityNotFoundError
from domain.model.order import InvalidStatusTransitionError, OrderStatus
from domain.model.stock import InsufficientStockError
from domain.schema.order import (
    CustomerInput,
    OrderCancel,
    OrderCreate,
    OrderItemInput,
    OrderUpdate,
)
from domain.schema.page import PageQuery
from domain.schema.product import ProductCreate, ProductUpdate
from domain.service.order import OrderService
from domain.service.product import ProductService
from tests.fakes.unit_of_work import InMemoryDatabase

CLIENTE = CustomerInput(name="Marina Duarte", email="marina@exemplo.com")


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def products(database: InMemoryDatabase) -> ProductService:
    return ProductService(database)


@pytest.fixture
def orders(database: InMemoryDatabase) -> OrderService:
    return OrderService(database)


async def novo_produto(
    service: ProductService,
    *,
    sku: str = "CAF-500",
    price: int = 3290,
    stock: int = 10,
):
    return await service.create(
        ProductCreate(
            sku=sku,
            name=f"Produto {sku}",
            description="",
            price_in_cents=price,
            initial_stock=stock,
        )
    )


def pedido(product_id, quantity: int = 2) -> OrderCreate:
    return OrderCreate(
        customer=CLIENTE,
        items=[OrderItemInput(product_id=product_id, quantity=quantity)],
    )


# -- criacao ----------------------------------------------------------------
async def test_criar_pedido_reserva_o_estoque(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=10)

    order = await orders.create(pedido(product.id, quantity=3))

    assert order.status is OrderStatus.PENDING
    assert order.reference.startswith("PED-")
    assert order.total_in_cents == 3 * 3290

    stock = database.stock[product.id]
    assert stock.quantity_on_hand == 10  # nada saiu do deposito ainda
    assert stock.quantity_reserved == 3
    assert stock.quantity_available == 7


async def test_preco_vem_do_catalogo_e_nao_do_cliente(
    products: ProductService, orders: OrderService
) -> None:
    product = await novo_produto(products, price=9900)

    order = await orders.create(pedido(product.id, quantity=1))

    assert order.items[0].unit_price_in_cents == 9900


async def test_sem_saldo_o_pedido_nao_e_criado(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=2)

    with pytest.raises(InsufficientStockError) as exc_info:
        await orders.create(pedido(product.id, quantity=5))

    assert exc_info.value.available == 2
    # Nem pedido, nem reserva: a transacao inteira foi descartada.
    assert database.orders == {}
    assert database.stock[product.id].quantity_reserved == 0


async def test_item_repetido_vira_uma_linha_somada(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=10)

    order = await orders.create(
        OrderCreate(
            customer=CLIENTE,
            items=[
                OrderItemInput(product_id=product.id, quantity=2),
                OrderItemInput(product_id=product.id, quantity=3),
            ],
        )
    )

    assert len(order.items) == 1
    assert order.items[0].quantity == 5
    assert database.stock[product.id].quantity_reserved == 5


async def test_produto_inexistente_no_pedido(orders: OrderService) -> None:
    with pytest.raises(EntityNotFoundError, match="nao encontrado"):
        await orders.create(pedido(uuid4()))


async def test_produto_inativo_nao_pode_ser_vendido(
    products: ProductService, orders: OrderService
) -> None:
    product = await novo_produto(products)
    await products.update(product.id, ProductUpdate(active=False))

    with pytest.raises(BusinessRuleViolationError, match="inativo"):
        await orders.create(pedido(product.id))


# -- alteracao --------------------------------------------------------------
async def test_alterar_itens_refaz_a_reserva(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=10)
    order = await orders.create(pedido(product.id, quantity=4))

    await orders.update(
        order.id,
        OrderUpdate(items=[OrderItemInput(product_id=product.id, quantity=6)]),
    )

    # A reserva antiga precisa voltar antes da nova, senao o pedido competiria
    # consigo mesmo pelo saldo.
    assert database.stock[product.id].quantity_reserved == 6


async def test_nao_altera_itens_de_pedido_confirmado(
    products: ProductService, orders: OrderService
) -> None:
    product = await novo_produto(products)
    order = await orders.create(pedido(product.id))
    await orders.confirm(order.id)

    with pytest.raises(BusinessRuleViolationError, match="nao podem ser alterados"):
        await orders.update(
            order.id, OrderUpdate(items=[OrderItemInput(product_id=product.id, quantity=1)])
        )


# -- ciclo de vida ----------------------------------------------------------
async def test_envio_baixa_o_estoque_reservado(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=10)
    order = await orders.create(pedido(product.id, quantity=3))

    await orders.confirm(order.id)
    await orders.ship(order.id)

    stock = database.stock[product.id]
    assert stock.quantity_on_hand == 7  # agora sim a mercadoria saiu
    assert stock.quantity_reserved == 0


async def test_fluxo_completo_ate_a_entrega(products: ProductService, orders: OrderService) -> None:
    product = await novo_produto(products)
    order = await orders.create(pedido(product.id))

    await orders.confirm(order.id)
    await orders.ship(order.id)
    delivered = await orders.deliver(order.id)

    assert delivered.status is OrderStatus.DELIVERED


async def test_cancelamento_libera_a_reserva(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products, stock=10)
    order = await orders.create(pedido(product.id, quantity=4))

    cancelled = await orders.cancel(order.id, OrderCancel(reason="Cliente desistiu"))

    assert cancelled.status is OrderStatus.CANCELLED
    assert cancelled.cancellation_reason == "Cliente desistiu"
    stock = database.stock[product.id]
    assert stock.quantity_reserved == 0
    assert stock.quantity_available == 10


async def test_nao_cancela_pedido_ja_enviado(
    products: ProductService, orders: OrderService
) -> None:
    product = await novo_produto(products)
    order = await orders.create(pedido(product.id))
    await orders.confirm(order.id)
    await orders.ship(order.id)

    with pytest.raises(InvalidStatusTransitionError):
        await orders.cancel(order.id, OrderCancel(reason="Tarde demais"))


async def test_estoque_liberado_volta_a_ser_vendavel(
    products: ProductService, orders: OrderService
) -> None:
    product = await novo_produto(products, stock=5)
    primeiro = await orders.create(pedido(product.id, quantity=5))

    with pytest.raises(InsufficientStockError):
        await orders.create(pedido(product.id, quantity=1))

    await orders.cancel(primeiro.id, OrderCancel(reason="Desistencia"))
    segundo = await orders.create(pedido(product.id, quantity=5))

    assert segundo.status is OrderStatus.PENDING


# -- listagem e exclusao ----------------------------------------------------
async def test_listagem_filtra_por_status(products: ProductService, orders: OrderService) -> None:
    product = await novo_produto(products, stock=20)
    primeiro = await orders.create(pedido(product.id, quantity=1))
    await orders.create(pedido(product.id, quantity=1))
    await orders.confirm(primeiro.id)

    page = await orders.paginate(page_query=PageQuery(), status=OrderStatus.CONFIRMED)

    assert page.total == 1
    assert page.items[0].id == primeiro.id


async def test_listagem_busca_por_cliente(products: ProductService, orders: OrderService) -> None:
    product = await novo_produto(products, stock=20)
    await orders.create(pedido(product.id, quantity=1))

    page = await orders.paginate(page_query=PageQuery(), search="marina")

    assert page.total == 1
    assert page.items[0].customer_name == "Marina Duarte"


async def test_so_exclui_pedido_cancelado(
    products: ProductService, orders: OrderService, database: InMemoryDatabase
) -> None:
    product = await novo_produto(products)
    order = await orders.create(pedido(product.id))

    with pytest.raises(BusinessRuleViolationError, match="cancelados"):
        await orders.delete(order.id)

    await orders.cancel(order.id, OrderCancel(reason="Duplicidade"))
    await orders.delete(order.id)

    assert order.id not in database.orders
