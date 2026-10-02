"""Controle de estoque."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from api.deps import PageQueryDep, StockServiceDep
from domain.schema.page import Page
from domain.schema.stock import StockAdjust, StockRead, StockReceive

router = APIRouter(prefix="/stock", tags=["estoque"])


@router.get("", response_model=Page[StockRead], summary="Lista os saldos")
async def list_stock(service: StockServiceDep, page_query: PageQueryDep) -> Page[StockRead]:
    return await service.paginate(page_query=page_query)


@router.get(
    "/{product_id}",
    response_model=StockRead,
    summary="Saldo de um produto",
    description="Disponivel = em maos - reservado.",
)
async def get_stock(product_id: UUID, service: StockServiceDep) -> StockRead:
    return await service.get(product_id)


@router.post(
    "/{product_id}/receipts",
    response_model=StockRead,
    summary="Registra entrada de mercadoria",
)
async def receive_stock(
    product_id: UUID, payload: StockReceive, service: StockServiceDep
) -> StockRead:
    return await service.receive(product_id, payload)


@router.post(
    "/{product_id}/adjustments",
    response_model=StockRead,
    summary="Ajusta o saldo apos inventario",
    description="Recusado se o novo saldo for menor que a quantidade reservada.",
)
async def adjust_stock(
    product_id: UUID, payload: StockAdjust, service: StockServiceDep
) -> StockRead:
    return await service.adjust(product_id, payload)
