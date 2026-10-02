"""Repositorio de pedidos sobre SQLAlchemy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.model.money import Money
from domain.model.order import Customer, Order, OrderItem, OrderStatus
from domain.repository.order import DailyOrders, OrderFilter, OrderStatistics
from infra.database.model.order import OrderItemTable, OrderTable

REFERENCE_PREFIX = "PED"


def _to_domain(row: OrderTable) -> Order:
    return Order(
        row.id,
        reference=row.reference,
        customer=Customer(name=row.customer_name, email=row.customer_email),
        items=[
            OrderItem(
                product_id=item.product_id,
                sku=item.sku,
                description=item.description,
                quantity=item.quantity,
                unit_price=Money(item.unit_price_in_cents, item.currency),
            )
            for item in row.items
        ],
        status=OrderStatus(row.status),
        placed_at=row.placed_at,
        updated_at=row.updated_at,
        cancellation_reason=row.cancellation_reason,
        version=row.version,
    )


class SqlAlchemyOrderRepository:
    """Traduz entre `Order` e as tabelas `orders` / `order_items`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, order_id: UUID) -> Order | None:
        row = await self._session.get(OrderTable, order_id)
        return None if row is None else _to_domain(row)

    async def get_by_reference(self, reference: str) -> Order | None:
        statement = select(OrderTable).where(OrderTable.reference == reference)
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else _to_domain(row)

    async def paginate(
        self, *, filters: OrderFilter, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        statement = select(OrderTable)

        if filters.status is not None:
            statement = statement.where(OrderTable.status == filters.status.value)
        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            statement = statement.where(
                OrderTable.reference.ilike(pattern) | OrderTable.customer_name.ilike(pattern)
            )

        total_statement = select(func.count()).select_from(statement.subquery())
        total = (await self._session.execute(total_statement)).scalar_one()

        statement = statement.order_by(OrderTable.placed_at.desc()).offset(offset).limit(limit)
        rows = (await self._session.execute(statement)).scalars().unique().all()

        return [_to_domain(row) for row in rows], total

    async def statistics(self) -> OrderStatistics:
        """Contagens por status e faturamento, em duas consultas agregadas."""
        by_status_rows = (
            await self._session.execute(
                select(OrderTable.status, func.count()).group_by(OrderTable.status)
            )
        ).all()
        by_status = {OrderStatus(status): count for status, count in by_status_rows}

        # Pedido cancelado nao entra no faturamento.
        revenue = (
            await self._session.execute(
                select(
                    func.coalesce(
                        func.sum(OrderItemTable.quantity * OrderItemTable.unit_price_in_cents),
                        0,
                    )
                )
                .select_from(OrderItemTable)
                .join(OrderTable, OrderTable.id == OrderItemTable.order_id)
                .where(OrderTable.status != OrderStatus.CANCELLED.value)
            )
        ).scalar_one()

        return OrderStatistics(
            total=sum(by_status.values()),
            by_status=by_status,
            revenue_in_cents=int(revenue),
        )

    async def daily_totals(self, *, days: int) -> list[DailyOrders]:
        """Um SELECT agregado por dia, em vez de carregar os pedidos na memoria."""
        since = datetime.now(UTC) - timedelta(days=days - 1)
        day = sa.cast(OrderTable.placed_at, sa.Date).label("dia")

        statement = (
            select(
                day,
                # DISTINCT porque o join com as linhas multiplica o pedido.
                func.count(sa.distinct(OrderTable.id)),
                func.coalesce(
                    func.sum(
                        sa.case(
                            (
                                OrderTable.status != OrderStatus.CANCELLED.value,
                                OrderItemTable.quantity * OrderItemTable.unit_price_in_cents,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(OrderTable)
            .outerjoin(OrderItemTable, OrderItemTable.order_id == OrderTable.id)
            .where(OrderTable.placed_at >= since)
            .group_by(day)
            .order_by(day)
        )

        rows = (await self._session.execute(statement)).all()
        return [
            DailyOrders(day=row[0], orders=int(row[1]), revenue_in_cents=int(row[2]))
            for row in rows
        ]

    async def recent(self, limit: int) -> list[Order]:
        statement = select(OrderTable).order_by(OrderTable.placed_at.desc()).limit(limit)
        rows = (await self._session.execute(statement)).scalars().unique().all()
        return [_to_domain(row) for row in rows]

    async def next_reference(self) -> str:
        """Proxima referencia legivel para humanos.

        Derivada da contagem de pedidos; a unicidade real e garantida pelo
        indice unico em `orders.reference`, nao por este calculo.
        """
        total = (
            await self._session.execute(select(func.count()).select_from(OrderTable))
        ).scalar_one()
        return f"{REFERENCE_PREFIX}-{total + 1:06d}"

    async def add(self, order: Order) -> None:
        self._session.add(
            OrderTable(
                id=order.id,
                reference=order.reference,
                status=order.status.value,
                customer_name=order.customer.name,
                customer_email=order.customer.email,
                currency=order.total.currency,
                cancellation_reason=order.cancellation_reason,
                version=order.version,
                placed_at=order.placed_at,
                updated_at=order.updated_at,
                items=[self._to_row(item, position) for position, item in enumerate(order.items)],
            )
        )

    async def save(self, order: Order) -> None:
        row = await self._session.get(OrderTable, order.id)
        if row is None:  # pragma: no cover - o service garante a existencia
            return

        row.status = order.status.value
        row.customer_name = order.customer.name
        row.customer_email = order.customer.email
        row.cancellation_reason = order.cancellation_reason
        row.updated_at = order.updated_at
        row.version = order.version + 1

        # Linhas sao substituidas em bloco: o agregado ja validou o conjunto
        # inteiro, e `delete-orphan` remove as que sairam.
        row.items = [self._to_row(item, position) for position, item in enumerate(order.items)]

    async def delete(self, order: Order) -> None:
        row = await self._session.get(OrderTable, order.id)
        if row is not None:
            await self._session.delete(row)

    @staticmethod
    def _to_row(item: OrderItem, position: int) -> OrderItemTable:
        return OrderItemTable(
            id=uuid4(),
            product_id=item.product_id,
            position=position,
            sku=item.sku,
            description=item.description,
            quantity=item.quantity,
            unit_price_in_cents=item.unit_price.amount_in_cents,
            currency=item.unit_price.currency,
        )
