"""Repositorios contra o Postgres real.

Os testes de service usam dubles em memoria; estes provam que o mapeamento
objeto-relacional tambem esta correto - que o que foi gravado volta igual.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from domain.model.money import Money
from domain.model.order import Customer, Order, OrderItem, OrderStatus
from domain.model.product import Product
from domain.model.stock import StockItem
from domain.repository.order import OrderFilter
from domain.repository.product import ProductFilter

pytestmark = pytest.mark.integration


async def test_produto_gravado_volta_identico(unit_of_work_factory) -> None:
    product = Product.create(
        sku="CAF-500", name="Cafe 500g", description="Pacote", price=Money(3290)
    )

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        loaded = await uow.products.get(product.id)

    assert loaded is not None
    assert loaded.sku == "CAF-500"
    assert loaded.price == Money(3290)
    assert loaded.is_active is True


async def test_busca_por_sku_e_case_insensitive(unit_of_work_factory) -> None:
    product = Product.create(sku="CAF-500", name="Cafe", description="", price=Money(100))

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        assert await uow.products.get_by_sku("caf-500") is not None


async def test_listagem_filtra_e_conta_o_total(unit_of_work_factory) -> None:
    async with unit_of_work_factory() as uow:
        for index in range(5):
            await uow.products.add(
                Product.create(
                    sku=f"SKU-{index:03d}",
                    name="Cafe especial" if index < 2 else "Cha verde",
                    description="",
                    price=Money(1000),
                )
            )
        await uow.commit()

    async with unit_of_work_factory() as uow:
        items, total = await uow.products.paginate(
            filters=ProductFilter(search="cafe"), offset=0, limit=10
        )

    assert total == 2
    assert len(items) == 2


async def test_rollback_descarta_a_escrita(unit_of_work_factory) -> None:
    product = Product.create(sku="TMP-001", name="Temporario", description="", price=Money(1))

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        # Sai do contexto sem commit.

    async with unit_of_work_factory() as uow:
        assert await uow.products.get(product.id) is None


async def test_estoque_preserva_saldo_e_reserva(unit_of_work_factory) -> None:
    product = Product.create(sku="CAF-500", name="Cafe", description="", price=Money(100))
    stock = StockItem(product.id, sku=product.sku)
    stock.receive(10)
    stock.reserve(3)

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        await uow.stock.add(stock)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        loaded = await uow.stock.get(product.id)

    assert loaded is not None
    assert loaded.quantity_on_hand == 10
    assert loaded.quantity_reserved == 3
    assert loaded.quantity_available == 7


async def test_pedido_volta_com_todas_as_linhas(unit_of_work_factory) -> None:
    product = Product.create(sku="CAF-500", name="Cafe", description="", price=Money(3290))
    outro = Product.create(sku="CHA-100", name="Cha", description="", price=Money(2150))

    order = Order.place(
        reference="PED-000001",
        customer=Customer(name="Marina Duarte", email="marina@exemplo.com"),
        items=[
            OrderItem(
                product_id=product.id,
                sku=product.sku,
                description=product.name,
                quantity=2,
                unit_price=product.price,
            ),
            OrderItem(
                product_id=outro.id,
                sku=outro.sku,
                description=outro.name,
                quantity=1,
                unit_price=outro.price,
            ),
        ],
    )

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        await uow.products.add(outro)
        await uow.orders.add(order)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        loaded = await uow.orders.get(order.id)

    assert loaded is not None
    assert len(loaded.items) == 2
    assert loaded.total == Money(2 * 3290 + 2150)
    assert loaded.status is OrderStatus.PENDING


async def test_troca_de_linhas_remove_as_antigas(unit_of_work_factory) -> None:
    product = Product.create(sku="CAF-500", name="Cafe", description="", price=Money(3290))
    item = OrderItem(
        product_id=product.id,
        sku=product.sku,
        description=product.name,
        quantity=2,
        unit_price=product.price,
    )
    order = Order.place(
        reference="PED-000001",
        customer=Customer(name="Marina", email="marina@exemplo.com"),
        items=[item],
    )

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        await uow.orders.add(order)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        loaded = await uow.orders.get(order.id)
        assert loaded is not None
        loaded.replace_items([replace(item, quantity=7)])
        await uow.orders.save(loaded)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        reloaded = await uow.orders.get(order.id)

    assert reloaded is not None
    # `delete-orphan`: a linha antiga nao pode ficar para tras.
    assert len(reloaded.items) == 1
    assert reloaded.items[0].quantity == 7


async def test_referencia_avanca_a_cada_pedido(unit_of_work_factory) -> None:
    async with unit_of_work_factory() as uow:
        assert await uow.orders.next_reference() == "PED-000001"


async def test_filtro_por_status_no_banco(unit_of_work_factory) -> None:
    product = Product.create(sku="CAF-500", name="Cafe", description="", price=Money(100))

    async with unit_of_work_factory() as uow:
        await uow.products.add(product)
        for index in range(3):
            order = Order.place(
                reference=f"PED-{index:06d}",
                customer=Customer(name="Marina", email="marina@exemplo.com"),
                items=[
                    OrderItem(
                        product_id=product.id,
                        sku=product.sku,
                        description=product.name,
                        quantity=1,
                        unit_price=product.price,
                    )
                ],
            )
            if index == 0:
                order.confirm()
            await uow.orders.add(order)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        items, total = await uow.orders.paginate(
            filters=OrderFilter(status=OrderStatus.CONFIRMED), offset=0, limit=10
        )

    assert total == 1
    assert items[0].status is OrderStatus.CONFIRMED


async def test_produto_inexistente_devolve_none(unit_of_work_factory) -> None:
    async with unit_of_work_factory() as uow:
        assert await uow.products.get(uuid4()) is None
