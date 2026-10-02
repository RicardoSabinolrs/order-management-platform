"""Versao 1 da API: endpoints de negocio."""

from fastapi import APIRouter

from api.v1 import auth, dashboard, orders, products, stock, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(products.router)
router.include_router(stock.router)
router.include_router(orders.router)
router.include_router(users.router)

__all__ = ["router"]
