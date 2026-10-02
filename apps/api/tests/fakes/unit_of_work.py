"""Unidade de trabalho em memoria.

Implementa as mesmas portas que o SQLAlchemy implementa, e por isso os testes
de service exercitam a logica de negocio de verdade - sem banco, em
milissegundos. Se um service so passasse com um mock que devolve o que ele
espera, o teste nao provaria nada.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from types import TracebackType
from typing import Self
from uuid import UUID

from domain.model.order import Order, OrderStatus
from domain.model.product import Product
from domain.model.stock import StockItem
from domain.model.user import User
from domain.repository.order import DailyOrders, OrderFilter, OrderStatistics
from domain.repository.product import ProductFilter
from domain.repository.stock import StockOverview
from domain.repository.user import UserRepository
from infra.repository.user import CompositeUserRepository, SettingsUserRepository


class FakeProductRepository:
    def __init__(self, storage: dict[UUID, Product]) -> None:
        self._storage = storage

    async def get(self, product_id: UUID) -> Product | None:
        return self._storage.get(product_id)

    async def get_by_sku(self, sku: str) -> Product | None:
        normalized = sku.strip().upper()
        return next((p for p in self._storage.values() if p.sku == normalized), None)

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, Product]:
        return {pid: self._storage[pid] for pid in product_ids if pid in self._storage}

    async def paginate(
        self, *, filters: ProductFilter, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        found = list(self._storage.values())
        if filters.active is not None:
            found = [p for p in found if p.is_active is filters.active]
        if filters.search:
            needle = filters.search.lower()
            found = [p for p in found if needle in p.name.lower() or needle in p.sku.lower()]
        found.sort(key=lambda product: product.sku)
        return found[offset : offset + limit], len(found)

    async def counts(self) -> tuple[int, int]:
        return len(self._storage), sum(1 for p in self._storage.values() if p.is_active)

    async def add(self, product: Product) -> None:
        self._storage[product.id] = product

    async def save(self, product: Product) -> None:
        self._storage[product.id] = product

    async def delete(self, product: Product) -> None:
        self._storage.pop(product.id, None)


class FakeStockRepository:
    def __init__(self, storage: dict[UUID, StockItem]) -> None:
        self._storage = storage

    async def get(self, product_id: UUID) -> StockItem | None:
        return self._storage.get(product_id)

    async def get_for_update(self, product_id: UUID) -> StockItem | None:
        # Sem concorrencia real em memoria: o lock nao muda o resultado aqui.
        return self._storage.get(product_id)

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, StockItem]:
        return {pid: self._storage[pid] for pid in product_ids if pid in self._storage}

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[StockItem], int]:
        found = sorted(self._storage.values(), key=lambda item: item.sku)
        return found[offset : offset + limit], len(found)

    async def overview(self) -> StockOverview:
        items = self._storage.values()
        return StockOverview(
            units_on_hand=sum(item.quantity_on_hand for item in items),
            units_reserved=sum(item.quantity_reserved for item in items),
            out_of_stock=sum(1 for item in items if item.quantity_available <= 0),
        )

    async def low_stock(self, *, threshold: int, limit: int) -> list[StockItem]:
        found = [item for item in self._storage.values() if item.quantity_available <= threshold]
        found.sort(key=lambda item: item.quantity_available)
        return found[:limit]

    async def add(self, stock: StockItem) -> None:
        self._storage[stock.product_id] = stock

    async def save(self, stock: StockItem) -> None:
        self._storage[stock.product_id] = stock


class FakeOrderRepository:
    def __init__(self, storage: dict[UUID, Order]) -> None:
        self._storage = storage

    async def get(self, order_id: UUID) -> Order | None:
        return self._storage.get(order_id)

    async def get_by_reference(self, reference: str) -> Order | None:
        return next((o for o in self._storage.values() if o.reference == reference), None)

    async def paginate(
        self, *, filters: OrderFilter, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        found = list(self._storage.values())
        if filters.status is not None:
            found = [o for o in found if o.status is filters.status]
        if filters.search:
            needle = filters.search.lower()
            found = [
                o
                for o in found
                if needle in o.reference.lower() or needle in o.customer.name.lower()
            ]
        found.sort(key=lambda order: order.placed_at, reverse=True)
        return found[offset : offset + limit], len(found)

    async def statistics(self) -> OrderStatistics:
        by_status: dict[OrderStatus, int] = {}
        revenue = 0
        for order in self._storage.values():
            by_status[order.status] = by_status.get(order.status, 0) + 1
            if order.status is not OrderStatus.CANCELLED:
                revenue += order.total.amount_in_cents
        return OrderStatistics(
            total=len(self._storage), by_status=by_status, revenue_in_cents=revenue
        )

    async def daily_totals(self, *, days: int) -> list[DailyOrders]:
        agregado: dict[date, tuple[int, int]] = {}
        limite = datetime.now(UTC).date() - timedelta(days=days - 1)

        for order in self._storage.values():
            dia = order.placed_at.date()
            if dia < limite:
                continue
            pedidos, receita = agregado.get(dia, (0, 0))
            faturado = 0 if order.status is OrderStatus.CANCELLED else order.total.amount_in_cents
            agregado[dia] = (pedidos + 1, receita + faturado)

        return [
            DailyOrders(day=dia, orders=pedidos, revenue_in_cents=receita)
            for dia, (pedidos, receita) in sorted(agregado.items())
        ]

    async def recent(self, limit: int) -> list[Order]:
        found = sorted(self._storage.values(), key=lambda order: order.placed_at, reverse=True)
        return found[:limit]

    async def next_reference(self) -> str:
        return f"PED-{len(self._storage) + 1:06d}"

    async def add(self, order: Order) -> None:
        self._storage[order.id] = order

    async def save(self, order: Order) -> None:
        self._storage[order.id] = order

    async def delete(self, order: Order) -> None:
        self._storage.pop(order.id, None)


class FakeUserRepository:
    def __init__(self, storage: dict[str, User]) -> None:
        self._storage = storage

    async def get(self, user_id: str) -> User | None:
        return self._storage.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        return next((u for u in self._storage.values() if u.email == normalized), None)

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        found = sorted(self._storage.values(), key=lambda user: (user.name, user.email))
        return found[offset : offset + limit], len(found)

    async def add(self, user: User) -> None:
        self._storage[user.id] = user


class FakeUnitOfWork:
    """Transacao simulada.

    `committed` conta os commits: e como os testes verificam que a operacao
    realmente fechou a transacao, e nao apenas montou os objetos.
    """

    def __init__(
        self,
        products: dict[UUID, Product],
        stock: dict[UUID, StockItem],
        orders: dict[UUID, Order],
        users: dict[str, User],
        root_users: SettingsUserRepository | None = None,
    ) -> None:
        self.products = FakeProductRepository(products)
        self.stock = FakeStockRepository(stock)
        self.orders = FakeOrderRepository(orders)
        # A composicao com o admin raiz e a mesma de producao: so a tabela e
        # trocada pelo dicionario.
        stored_users = FakeUserRepository(users)
        self.users: UserRepository = (
            stored_users
            if root_users is None
            else CompositeUserRepository(root_users, stored_users)
        )
        self.committed = 0
        self.rolled_back = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed += 1

    async def rollback(self) -> None:
        self.rolled_back += 1


class InMemoryDatabase:
    """Armazenamento compartilhado entre as transacoes de um teste."""

    def __init__(self, root_users: SettingsUserRepository | None = None) -> None:
        self.products: dict[UUID, Product] = {}
        self.stock: dict[UUID, StockItem] = {}
        self.orders: dict[UUID, Order] = {}
        self.users: dict[str, User] = {}
        self.root_users = root_users
        self.units: list[FakeUnitOfWork] = []

    def __call__(self) -> FakeUnitOfWork:
        unit = FakeUnitOfWork(
            self.products, self.stock, self.orders, self.users, root_users=self.root_users
        )
        self.units.append(unit)
        return unit

    @property
    def commits(self) -> int:
        return sum(unit.committed for unit in self.units)

    def order_by_status(self, status: OrderStatus) -> list[Order]:
        return [order for order in self.orders.values() if order.status is status]


def unit_of_work_factory() -> Callable[[], FakeUnitOfWork]:
    """Fabrica pronta para injetar nos services."""
    return InMemoryDatabase()
