"""Regras de controle de estoque."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from domain.exception import EntityNotFoundError
from domain.model.stock import StockItem
from domain.repository.base import UnitOfWork
from domain.schema.page import Page, PageQuery
from domain.schema.stock import StockAdjust, StockRead, StockReceive


class StockService:
    """Entrada, ajuste e consulta de saldo.

    Reserva e baixa nao aparecem aqui: elas sao efeitos de operacoes sobre
    pedidos e pertencem ao `OrderService`, que as executa na mesma transacao da
    mudanca de status.
    """

    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work_factory

    async def get(self, product_id: UUID) -> StockRead:
        async with self._unit_of_work() as uow:
            return StockRead.from_domain(await self._require(uow, product_id))

    async def paginate(self, *, page_query: PageQuery) -> Page[StockRead]:
        async with self._unit_of_work() as uow:
            items, total = await uow.stock.paginate(
                offset=page_query.offset, limit=page_query.page_size
            )
            return Page[StockRead](
                items=[StockRead.from_domain(item) for item in items],
                total=total,
                page=page_query.page,
                page_size=page_query.page_size,
            )

    async def receive(self, product_id: UUID, payload: StockReceive) -> StockRead:
        """Registra entrada de mercadoria."""
        async with self._unit_of_work() as uow:
            stock = await self._require_for_update(uow, product_id)
            stock.receive(payload.quantity)
            await uow.stock.save(stock)
            await uow.commit()
            return StockRead.from_domain(stock)

    async def adjust(self, product_id: UUID, payload: StockAdjust) -> StockRead:
        """Corrige o saldo fisico apos inventario."""
        async with self._unit_of_work() as uow:
            stock = await self._require_for_update(uow, product_id)
            stock.adjust_to(payload.quantity_on_hand, reason=payload.reason)
            await uow.stock.save(stock)
            await uow.commit()
            return StockRead.from_domain(stock)

    @staticmethod
    async def _require(uow: UnitOfWork, product_id: UUID) -> StockItem:
        stock = await uow.stock.get(product_id)
        if stock is None:
            msg = f"Nao ha registro de estoque para o produto {product_id}."
            raise EntityNotFoundError(msg)
        return stock

    @staticmethod
    async def _require_for_update(uow: UnitOfWork, product_id: UUID) -> StockItem:
        stock = await uow.stock.get_for_update(product_id)
        if stock is None:
            msg = f"Nao ha registro de estoque para o produto {product_id}."
            raise EntityNotFoundError(msg)
        return stock
