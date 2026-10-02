"""Repositorio de produtos sobre SQLAlchemy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.model.money import Money
from domain.model.product import Product
from domain.repository.product import ProductFilter
from infra.database.model.product import ProductTable


def _to_domain(row: ProductTable) -> Product:
    return Product(
        row.id,
        sku=row.sku,
        name=row.name,
        description=row.description,
        price=Money(row.price_in_cents, row.currency),
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


class SqlAlchemyProductRepository:
    """Traduz entre `Product` e a tabela `products`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: UUID) -> Product | None:
        row = await self._session.get(ProductTable, product_id)
        return None if row is None else _to_domain(row)

    async def get_by_sku(self, sku: str) -> Product | None:
        statement = select(ProductTable).where(ProductTable.sku == sku.strip().upper())
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else _to_domain(row)

    async def get_many(self, product_ids: list[UUID]) -> dict[UUID, Product]:
        if not product_ids:
            return {}
        statement = select(ProductTable).where(ProductTable.id.in_(product_ids))
        rows = (await self._session.execute(statement)).scalars().all()
        return {row.id: _to_domain(row) for row in rows}

    async def paginate(
        self, *, filters: ProductFilter, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        statement = select(ProductTable)

        if filters.active is not None:
            statement = statement.where(ProductTable.active.is_(filters.active))
        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            statement = statement.where(
                ProductTable.name.ilike(pattern) | ProductTable.sku.ilike(pattern)
            )

        # O total e contado sobre o mesmo filtro, sem offset/limit: e quantos
        # registros existem, nao quantos vieram nesta pagina.
        total_statement = select(func.count()).select_from(statement.subquery())
        total = (await self._session.execute(total_statement)).scalar_one()

        statement = statement.order_by(ProductTable.sku).offset(offset).limit(limit)
        rows = (await self._session.execute(statement)).scalars().all()

        return [_to_domain(row) for row in rows], total

    async def counts(self) -> tuple[int, int]:
        row = (
            await self._session.execute(
                select(
                    func.count(),
                    func.count().filter(ProductTable.active.is_(True)),
                ).select_from(ProductTable)
            )
        ).one()
        return int(row[0]), int(row[1])

    async def add(self, product: Product) -> None:
        self._session.add(
            ProductTable(
                id=product.id,
                sku=product.sku,
                name=product.name,
                description=product.description,
                price_in_cents=product.price.amount_in_cents,
                currency=product.price.currency,
                active=product.is_active,
                version=product.version,
                created_at=product.created_at,
                updated_at=product.updated_at,
            )
        )

    async def save(self, product: Product) -> None:
        row = await self._session.get(ProductTable, product.id)
        if row is None:  # pragma: no cover - o service garante a existencia
            return
        row.name = product.name
        row.description = product.description
        row.price_in_cents = product.price.amount_in_cents
        row.currency = product.price.currency
        row.active = product.is_active
        row.updated_at = product.updated_at
        row.version = product.version + 1

    async def delete(self, product: Product) -> None:
        row = await self._session.get(ProductTable, product.id)
        if row is not None:
            await self._session.delete(row)
