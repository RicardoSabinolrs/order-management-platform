"""Portas de persistencia implementadas por `infra/repository`."""

from domain.repository.base import UnitOfWork
from domain.repository.health import HealthRepository
from domain.repository.order import OrderFilter, OrderRepository, OrderStatistics
from domain.repository.product import ProductFilter, ProductRepository
from domain.repository.stock import StockOverview, StockRepository
from domain.repository.user import UserRepository

__all__ = [
    "HealthRepository",
    "OrderFilter",
    "OrderRepository",
    "OrderStatistics",
    "ProductFilter",
    "ProductRepository",
    "StockOverview",
    "StockRepository",
    "UnitOfWork",
    "UserRepository",
]
