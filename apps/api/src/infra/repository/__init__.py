"""Implementacoes concretas das portas de `domain/repository`."""

from infra.repository.health import PostgresHealthRepository
from infra.repository.order import SqlAlchemyOrderRepository
from infra.repository.product import SqlAlchemyProductRepository
from infra.repository.stock import SqlAlchemyStockRepository
from infra.repository.user import (
    CompositeUserRepository,
    SettingsUserRepository,
    SqlAlchemyUserRepository,
)

__all__ = [
    "CompositeUserRepository",
    "PostgresHealthRepository",
    "SettingsUserRepository",
    "SqlAlchemyOrderRepository",
    "SqlAlchemyProductRepository",
    "SqlAlchemyStockRepository",
    "SqlAlchemyUserRepository",
]
