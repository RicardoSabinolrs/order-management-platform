"""Repositorio de estoque sobre SQLAlchemy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.model.stock import StockItem
from domain.repository.stock import StockOverview
from infra.database.model.stock import StockItemTable


def _to_domain(row: StockItemTable) -> StockItem:
    return StockItem(
        row.product_id,
        sku=row.sku,
        quantity_on_hand=row.quantity_on_hand,
        quantity_reserved=row.quantity_reserved,
        updated_at=row.updated_at,
        version=row.version,
    )


class SqlAlchemyStockRepository:
    """Traduz entre `StockItem` e a tabela `stock_items`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: UUID) -> StockItem | None:
        row = await self._session.get(StockItemTable, product_id)
        return None if row is None else _to_domain(row)

    async def get_for_update(self, product_id: UUID) -> StockItem | None:
        """Le o saldo com `SELECT ... FOR UPDATE`.

        Segura a linha ate o commit: a segunda transacao que tentar reservar o
        mesmo produto espera, le o saldo ja atualizado e decide sobre o valor
        correto. Sem isso, duas reservas simultaneas leem o mesmo saldo e
        vendem a mesma unidade duas vezes.
        """
        statement = (
            select(StockItemTable).where(StockItemTable.product_id == product_id).with_for_update()
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else _to_domain(row)

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, StockItem]:
        if not product_ids:
            return {}
        statement = select(StockItemTable).where(StockItemTable.product_id.in_(product_ids))
        rows = (await self._session.execute(statement)).scalars().all()
        return {row.product_id: _to_domain(row) for row in rows}

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[StockItem], int]:
        total = (
            await self._session.execute(select(func.count()).select_from(StockItemTable))
        ).scalar_one()

        statement = select(StockItemTable).order_by(StockItemTable.sku).offset(offset).limit(limit)
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_domain(row) for row in rows], total

    async def overview(self) -> StockOverview:
        available = StockItemTable.quantity_on_hand - StockItemTable.quantity_reserved
        row = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(StockItemTable.quantity_on_hand), 0),
                    func.coalesce(func.sum(StockItemTable.quantity_reserved), 0),
                    func.count().filter(available <= 0),
                ).select_from(StockItemTable)
            )
        ).one()
        return StockOverview(
            units_on_hand=int(row[0]), units_reserved=int(row[1]), out_of_stock=int(row[2])
        )

    async def low_stock(self, *, threshold: int, limit: int) -> list[StockItem]:
        available = StockItemTable.quantity_on_hand - StockItemTable.quantity_reserved
        statement = (
            select(StockItemTable)
            .where(available <= threshold)
            .order_by(available.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_domain(row) for row in rows]

    async def add(self, stock: StockItem) -> None:
        self._session.add(
            StockItemTable(
                product_id=stock.product_id,
                sku=stock.sku,
                quantity_on_hand=stock.quantity_on_hand,
                quantity_reserved=stock.quantity_reserved,
                version=stock.version,
                updated_at=stock.updated_at,
            )
        )

    async def save(self, stock: StockItem) -> None:
        row = await self._session.get(StockItemTable, stock.product_id)
        if row is None:  # pragma: no cover - o service garante a existencia
            return
        row.quantity_on_hand = stock.quantity_on_hand
        row.quantity_reserved = stock.quantity_reserved
        row.updated_at = stock.updated_at
        row.version = stock.version + 1
