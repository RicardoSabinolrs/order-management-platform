"""Modelos de dominio: entidades, agregados, value objects e eventos."""

from domain.model.base import AggregateRoot, Entity, ValueObject
from domain.model.event import DomainEvent
from domain.model.money import DEFAULT_CURRENCY, Money
from domain.model.order import (
    ALLOWED_TRANSITIONS,
    Customer,
    InvalidStatusTransitionError,
    Order,
    OrderItem,
    OrderPlaced,
    OrderStatus,
    OrderStatusChanged,
)
from domain.model.product import Product, ProductCreated
from domain.model.stock import (
    InsufficientStockError,
    StockItem,
    StockMovementKind,
    StockMovementRecorded,
)
from domain.model.user import Role, User

__all__ = [
    "ALLOWED_TRANSITIONS",
    "DEFAULT_CURRENCY",
    "AggregateRoot",
    "Customer",
    "DomainEvent",
    "Entity",
    "InsufficientStockError",
    "InvalidStatusTransitionError",
    "Money",
    "Order",
    "OrderItem",
    "OrderPlaced",
    "OrderStatus",
    "OrderStatusChanged",
    "Product",
    "ProductCreated",
    "Role",
    "StockItem",
    "StockMovementKind",
    "StockMovementRecorded",
    "User",
    "ValueObject",
]
