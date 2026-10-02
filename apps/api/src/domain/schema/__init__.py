"""Schemas: contratos de entrada e saida dos services."""

from domain.schema.auth import LoginRequest, LoginResponse
from domain.schema.base import BaseSchema
from domain.schema.health import DependencyStatusSchema, LivenessSchema, ReadinessSchema
from domain.schema.order import (
    CustomerInput,
    CustomerRead,
    OrderCancel,
    OrderCreate,
    OrderItemInput,
    OrderItemRead,
    OrderRead,
    OrderSummary,
    OrderUpdate,
)
from domain.schema.page import Page, PageQuery
from domain.schema.product import ProductCreate, ProductRead, ProductUpdate
from domain.schema.stock import StockAdjust, StockRead, StockReceive
from domain.schema.token import TokenPayloadSchema, TokenSchema
from domain.schema.user import UserCreate, UserRead

__all__ = [
    "BaseSchema",
    "CustomerInput",
    "CustomerRead",
    "DependencyStatusSchema",
    "LivenessSchema",
    "LoginRequest",
    "LoginResponse",
    "OrderCancel",
    "OrderCreate",
    "OrderItemInput",
    "OrderItemRead",
    "OrderRead",
    "OrderSummary",
    "OrderUpdate",
    "Page",
    "PageQuery",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "ReadinessSchema",
    "StockAdjust",
    "StockRead",
    "StockReceive",
    "TokenPayloadSchema",
    "TokenSchema",
    "UserCreate",
    "UserRead",
]
