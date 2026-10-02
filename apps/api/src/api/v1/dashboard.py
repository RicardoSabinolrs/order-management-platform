"""Painel de controle."""

from __future__ import annotations

from fastapi import APIRouter

from api.deps import DashboardServiceDep
from domain.schema.dashboard import DashboardRead

router = APIRouter(prefix="/dashboard", tags=["painel"])


@router.get(
    "",
    response_model=DashboardRead,
    summary="Visao consolidada de pedidos e estoque",
)
async def overview(service: DashboardServiceDep) -> DashboardRead:
    return await service.overview()
