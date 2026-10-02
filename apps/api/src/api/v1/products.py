"""CRUD do catalogo de produtos."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from api.deps import PageQueryDep, ProductServiceDep
from domain.schema.page import Page
from domain.schema.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["produtos"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um produto",
    description="Cria o produto e o registro de estoque correspondente.",
)
async def create_product(payload: ProductCreate, service: ProductServiceDep) -> ProductRead:
    return await service.create(payload)


@router.get("", response_model=Page[ProductRead], summary="Lista os produtos")
async def list_products(
    service: ProductServiceDep,
    page_query: PageQueryDep,
    search: Annotated[str | None, Query(description="Busca por nome ou SKU.")] = None,
    active: Annotated[bool | None, Query(description="Filtra por situacao.")] = None,
) -> Page[ProductRead]:
    return await service.paginate(page_query=page_query, search=search, active=active)


@router.get("/{product_id}", response_model=ProductRead, summary="Detalha um produto")
async def get_product(product_id: UUID, service: ProductServiceDep) -> ProductRead:
    return await service.get(product_id)


@router.patch("/{product_id}", response_model=ProductRead, summary="Altera um produto")
async def update_product(
    product_id: UUID, payload: ProductUpdate, service: ProductServiceDep
) -> ProductRead:
    return await service.update(product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um produto",
    description="Recusado quando ha estoque reservado em pedidos.",
)
async def delete_product(product_id: UUID, service: ProductServiceDep) -> Response:
    await service.delete(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
