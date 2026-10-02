"""CRUD e ciclo de vida dos pedidos."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from api.deps import OrderServiceDep, PageQueryDep
from domain.model.order import OrderStatus
from domain.schema.order import (
    OrderCancel,
    OrderCreate,
    OrderRead,
    OrderSummary,
    OrderUpdate,
)
from domain.schema.page import Page

router = APIRouter(prefix="/orders", tags=["pedidos"])


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um pedido",
    description="Reserva o estoque de todos os itens. Falta de saldo devolve 409.",
)
async def create_order(payload: OrderCreate, service: OrderServiceDep) -> OrderRead:
    return await service.create(payload)


@router.get("", response_model=Page[OrderSummary], summary="Lista os pedidos")
async def list_orders(
    service: OrderServiceDep,
    page_query: PageQueryDep,
    order_status: Annotated[
        OrderStatus | None, Query(alias="status", description="Filtra por status.")
    ] = None,
    search: Annotated[
        str | None, Query(description="Busca por referencia ou nome do cliente.")
    ] = None,
) -> Page[OrderSummary]:
    return await service.paginate(page_query=page_query, status=order_status, search=search)


@router.get("/{order_id}", response_model=OrderRead, summary="Detalha um pedido")
async def get_order(order_id: UUID, service: OrderServiceDep) -> OrderRead:
    return await service.get(order_id)


@router.patch(
    "/{order_id}",
    response_model=OrderRead,
    summary="Altera um pedido pendente",
    description="Trocar os itens refaz a reserva de estoque.",
)
async def update_order(order_id: UUID, payload: OrderUpdate, service: OrderServiceDep) -> OrderRead:
    return await service.update(order_id, payload)


@router.post("/{order_id}/confirm", response_model=OrderRead, summary="Confirma o pedido")
async def confirm_order(order_id: UUID, service: OrderServiceDep) -> OrderRead:
    return await service.confirm(order_id)


@router.post(
    "/{order_id}/ship",
    response_model=OrderRead,
    summary="Registra o envio",
    description="Baixa definitivamente o estoque reservado.",
)
async def ship_order(order_id: UUID, service: OrderServiceDep) -> OrderRead:
    return await service.ship(order_id)


@router.post("/{order_id}/deliver", response_model=OrderRead, summary="Conclui o pedido")
async def deliver_order(order_id: UUID, service: OrderServiceDep) -> OrderRead:
    return await service.deliver(order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancela o pedido",
    description="Libera o estoque reservado.",
)
async def cancel_order(order_id: UUID, payload: OrderCancel, service: OrderServiceDep) -> OrderRead:
    return await service.cancel(order_id, payload)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um pedido cancelado",
)
async def delete_order(order_id: UUID, service: OrderServiceDep) -> Response:
    await service.delete(order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
