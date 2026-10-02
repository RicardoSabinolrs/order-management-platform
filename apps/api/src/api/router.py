"""Composicao dos routers da aplicacao."""

from __future__ import annotations

from fastapi import APIRouter

from api import health
from api.v1 import router as v1_router

# Sondas: caminho fixo, fora do schema publico da API.
infrastructure_router = APIRouter()
infrastructure_router.include_router(health.router, include_in_schema=False)

__all__ = ["infrastructure_router", "v1_router"]
