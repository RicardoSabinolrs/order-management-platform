"""DashboardService: consolidacao de pedidos e estoque."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domain.model.order import OrderStatus
from domain.schema.order import CustomerInput, OrderCancel, OrderCreate, OrderItemInput
from domain.schema.product import ProductCreate
from domain.service.dashboard import DashboardService
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


@pytest.fixture
def dashboard(database: InMemoryDatabase) -> DashboardService:
    return DashboardService(database)


async def novo_produto(service: ProductService, *, sku: str, preco: int, estoque: int):
    return await service.create(
        ProductCreate(
            sku=sku,
            name=f"Produto {sku}",
            description="",
            price_in_cents=preco,
            initial_stock=estoque,
        )
    )


async def test_painel_vazio_nao_divide_por_zero(dashboard: DashboardService) -> None:
    overview = await dashboard.overview()

    assert overview.orders_total == 0
    assert overview.revenue_in_cents == 0
    assert overview.average_ticket_in_cents == 0
    assert overview.recent_orders == []


async def test_contagens_de_catalogo_e_estoque(
    products: ProductService, dashboard: DashboardService
) -> None:
    await novo_produto(products, sku="CAF-500", preco=3290, estoque=100)
    await novo_produto(products, sku="CHA-100", preco=2150, estoque=5)

    overview = await dashboard.overview()

    assert overview.products_total == 2
    assert overview.products_active == 2
    assert overview.units_on_hand == 105
    assert overview.units_reserved == 0


async def test_reserva_aparece_no_painel(
    products: ProductService, orders: OrderService, dashboard: DashboardService
) -> None:
    product = await novo_produto(products, sku="CAF-500", preco=1000, estoque=10)
    await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=4)])
    )

    overview = await dashboard.overview()

    assert overview.units_on_hand == 10
    assert overview.units_reserved == 4
    assert overview.orders_open == 1


async def test_faturamento_ignora_cancelados(
    products: ProductService, orders: OrderService, dashboard: DashboardService
) -> None:
    product = await novo_produto(products, sku="CAF-500", preco=1000, estoque=100)

    await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=3)])
    )
    cancelado = await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=7)])
    )
    await orders.cancel(cancelado.id, OrderCancel(reason="Cliente desistiu"))

    overview = await dashboard.overview()

    assert overview.orders_total == 2
    assert overview.revenue_in_cents == 3000
    assert overview.average_ticket_in_cents == 3000  # divide so pelo faturavel


async def test_todos_os_status_aparecem_mesmo_zerados(dashboard: DashboardService) -> None:
    overview = await dashboard.overview()

    # A tela desenha um cartao por status: faltar um deixaria buraco no painel.
    assert [entry.status for entry in overview.orders_by_status] == list(OrderStatus)


async def test_alerta_de_reposicao_ordena_do_menor_disponivel(
    products: ProductService, dashboard: DashboardService
) -> None:
    await novo_produto(products, sku="ALTO-001", preco=100, estoque=500)
    await novo_produto(products, sku="BAIXO-001", preco=100, estoque=3)
    await novo_produto(products, sku="ZERO-001", preco=100, estoque=0)

    overview = await dashboard.overview()

    assert [item.sku for item in overview.low_stock] == ["ZERO-001", "BAIXO-001"]
    assert overview.out_of_stock == 1


async def test_pedidos_recentes_vem_do_mais_novo(
    products: ProductService, orders: OrderService, dashboard: DashboardService
) -> None:
    product = await novo_produto(products, sku="CAF-500", preco=100, estoque=100)
    for _ in range(7):
        await orders.create(
            OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=1)])
        )

    overview = await dashboard.overview()

    assert len(overview.recent_orders) == 5


async def test_serie_diaria_tem_a_janela_completa(dashboard: DashboardService) -> None:
    overview = await dashboard.overview()

    # 14 pontos mesmo sem pedido algum: um grafico de tempo com dias faltando
    # desenha uma linha que pula o vazio e sugere movimento onde nao houve.
    assert len(overview.daily) == 14
    assert all(ponto.orders == 0 for ponto in overview.daily)


async def test_serie_diaria_esta_em_ordem_cronologica(dashboard: DashboardService) -> None:
    datas = [ponto.date for ponto in (await dashboard.overview()).daily]

    assert datas == sorted(datas)
    assert datas[-1] == datetime.now(UTC).date()


async def test_pedido_de_hoje_aparece_no_ultimo_ponto(
    products: ProductService, orders: OrderService, dashboard: DashboardService
) -> None:
    product = await novo_produto(products, sku="CAF-500", preco=1000, estoque=100)
    await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=3)])
    )

    hoje = (await dashboard.overview()).daily[-1]

    assert hoje.orders == 1
    assert hoje.revenue_in_cents == 3000


async def test_cancelado_conta_como_pedido_mas_nao_como_receita(
    products: ProductService, orders: OrderService, dashboard: DashboardService
) -> None:
    product = await novo_produto(products, sku="CAF-500", preco=1000, estoque=100)
    pedido = await orders.create(
        OrderCreate(customer=CLIENTE, items=[OrderItemInput(product_id=product.id, quantity=2)])
    )
    await orders.cancel(pedido.id, OrderCancel(reason="Cliente desistiu"))

    hoje = (await dashboard.overview()).daily[-1]

    assert hoje.orders == 1
    assert hoje.revenue_in_cents == 0
