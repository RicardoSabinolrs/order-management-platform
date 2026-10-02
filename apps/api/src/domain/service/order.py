"""Regras de pedidos e sua interacao com o estoque."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from domain.exception import BusinessRuleViolationError, EntityNotFoundError
from domain.model.order import Customer, Order, OrderItem, OrderStatus
from domain.model.product import Product
from domain.model.stock import StockItem
from domain.repository.base import UnitOfWork
from domain.repository.order import OrderFilter
from domain.schema.order import (
    CustomerInput,
    OrderCancel,
    OrderCreate,
    OrderItemInput,
    OrderRead,
    OrderSummary,
    OrderUpdate,
)
from domain.schema.page import Page, PageQuery


class OrderService:
    """Ciclo de vida do pedido.

    Este service e o dono da relacao entre pedido e estoque:

    - criar    reserva o saldo de cada item;
    - alterar  devolve a reserva antiga e reserva a nova;
    - cancelar libera o que estava reservado;
    - enviar   baixa definitivamente o que estava reservado.

    Tudo isso acontece dentro da mesma transacao da mudanca do pedido. Se a
    reserva falhar, o pedido nao e criado - nao existe estado intermediario em
    que o pedido existe sem o estoque correspondente.
    """

    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work_factory

    # -- leitura ------------------------------------------------------------
    async def get(self, order_id: UUID) -> OrderRead:
        async with self._unit_of_work() as uow:
            return OrderRead.from_domain(await self._require(uow, order_id))

    async def paginate(
        self,
        *,
        page_query: PageQuery,
        status: OrderStatus | None = None,
        search: str | None = None,
    ) -> Page[OrderSummary]:
        async with self._unit_of_work() as uow:
            orders, total = await uow.orders.paginate(
                filters=OrderFilter(status=status, search=search),
                offset=page_query.offset,
                limit=page_query.page_size,
            )
            return Page[OrderSummary](
                items=[OrderSummary.from_domain(order) for order in orders],
                total=total,
                page=page_query.page,
                page_size=page_query.page_size,
            )

    # -- escrita ------------------------------------------------------------
    async def create(self, payload: OrderCreate) -> OrderRead:
        """Registra um pedido e reserva o estoque de todos os itens."""
        async with self._unit_of_work() as uow:
            items = await self._build_items(uow, payload.items)
            await self._reserve(uow, items)

            order = Order.place(
                reference=await uow.orders.next_reference(),
                customer=self._to_customer(payload.customer),
                items=items,
            )
            await uow.orders.add(order)

            await uow.commit()
            return OrderRead.from_domain(order)

    async def update(self, order_id: UUID, payload: OrderUpdate) -> OrderRead:
        """Altera um pedido ainda pendente."""
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)

            if payload.customer is not None:
                order.change_customer(self._to_customer(payload.customer))

            if payload.items is not None:
                # A reserva antiga volta ao disponivel antes de a nova ser
                # tentada; do contrario o proprio pedido competiria consigo
                # mesmo pelo saldo.
                await self._release(uow, order.items)
                new_items = await self._build_items(uow, payload.items)
                await self._reserve(uow, new_items)
                order.replace_items(new_items)

            await uow.orders.save(order)
            await uow.commit()
            return OrderRead.from_domain(order)

    async def confirm(self, order_id: UUID) -> OrderRead:
        """Confirma o pedido. O estoque ja esta reservado desde a criacao."""
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)
            order.confirm()
            await uow.orders.save(order)
            await uow.commit()
            return OrderRead.from_domain(order)

    async def ship(self, order_id: UUID) -> OrderRead:
        """Marca o envio e baixa o estoque reservado."""
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)
            order.ship()

            for item in order.items:
                stock = await self._require_stock(uow, item.product_id, item.sku)
                stock.ship(item.quantity)
                await uow.stock.save(stock)

            await uow.orders.save(order)
            await uow.commit()
            return OrderRead.from_domain(order)

    async def deliver(self, order_id: UUID) -> OrderRead:
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)
            order.deliver()
            await uow.orders.save(order)
            await uow.commit()
            return OrderRead.from_domain(order)

    async def cancel(self, order_id: UUID, payload: OrderCancel) -> OrderRead:
        """Cancela o pedido e devolve o saldo reservado ao disponivel."""
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)
            order.cancel(payload.reason)
            await self._release(uow, order.items)
            await uow.orders.save(order)
            await uow.commit()
            return OrderRead.from_domain(order)

    async def delete(self, order_id: UUID) -> None:
        """Remove um pedido cancelado do historico ativo.

        Apagar um pedido vivo destruiria a trilha de auditoria e deixaria a
        reserva de estoque pendurada; por isso so cancelados podem sair.
        """
        async with self._unit_of_work() as uow:
            order = await self._require(uow, order_id)
            if order.status is not OrderStatus.CANCELLED:
                msg = (
                    f"So pedidos cancelados podem ser excluidos. "
                    f"O pedido {order.reference} esta '{order.status.value}'."
                )
                raise BusinessRuleViolationError(msg)

            await uow.orders.delete(order)
            await uow.commit()

    # -- apoio --------------------------------------------------------------
    @staticmethod
    def _to_customer(payload: CustomerInput) -> Customer:
        return Customer(name=payload.name, email=payload.email)

    @staticmethod
    async def _build_items(uow: UnitOfWork, inputs: Sequence[OrderItemInput]) -> list[OrderItem]:
        """Transforma o payload em linhas do pedido, com os dados do catalogo.

        O preco vem sempre do produto, nunca do cliente: aceitar preco do
        payload permitiria comprar qualquer coisa por um centavo.
        """
        merged: dict[UUID, int] = {}
        for entry in inputs:
            # O mesmo produto repetido vira uma unica linha somada; duas linhas
            # do mesmo SKU reservariam estoque em duplicidade.
            merged[entry.product_id] = merged.get(entry.product_id, 0) + entry.quantity

        products = await uow.products.get_many(list(merged))
        missing = sorted(str(product_id) for product_id in merged if product_id not in products)
        if missing:
            msg = f"Produto(s) nao encontrado(s): {', '.join(missing)}."
            raise EntityNotFoundError(msg)

        inactive = sorted(product.sku for product in products.values() if not product.is_active)
        if inactive:
            msg = f"Produto(s) inativo(s) nao podem ser vendidos: {', '.join(inactive)}."
            raise BusinessRuleViolationError(msg)

        return [
            OrderService._to_item(products[product_id], quantity)
            for product_id, quantity in merged.items()
        ]

    @staticmethod
    def _to_item(product: Product, quantity: int) -> OrderItem:
        return OrderItem(
            product_id=product.id,
            sku=product.sku,
            description=product.name,
            quantity=quantity,
            unit_price=product.price,
        )

    @staticmethod
    async def _reserve(uow: UnitOfWork, items: Sequence[OrderItem]) -> None:
        for item in items:
            stock = await OrderService._require_stock(uow, item.product_id, item.sku)
            stock.reserve(item.quantity)
            await uow.stock.save(stock)

    @staticmethod
    async def _release(uow: UnitOfWork, items: Sequence[OrderItem]) -> None:
        for item in items:
            stock = await OrderService._require_stock(uow, item.product_id, item.sku)
            stock.release(item.quantity)
            await uow.stock.save(stock)

    @staticmethod
    async def _require_stock(uow: UnitOfWork, product_id: UUID, sku: str) -> StockItem:
        # `get_for_update` trava a linha: reservar e ler-decidir-escrever, e sem
        # o lock dois pedidos simultaneos venderiam a mesma unidade.
        stock = await uow.stock.get_for_update(product_id)
        if stock is None:
            msg = f"Nao ha registro de estoque para o SKU {sku}."
            raise EntityNotFoundError(msg)
        return stock

    @staticmethod
    async def _require(uow: UnitOfWork, order_id: UUID) -> Order:
        order = await uow.orders.get(order_id)
        if order is None:
            msg = f"Pedido {order_id} nao encontrado."
            raise EntityNotFoundError(msg)
        return order
