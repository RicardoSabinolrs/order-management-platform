"""Services: toda a logica de negocio da aplicacao.

Um endpoint recebe apenas o service de que precisa e devolve o que ele retorna.
Nenhuma regra, nenhum `if` de negocio e nenhum acesso a repositorio vive na
camada `api`.
"""

from domain.service.auth import AuthService
from domain.service.dashboard import DashboardService
from domain.service.health import HealthService
from domain.service.order import OrderService
from domain.service.product import DuplicateSkuError, ProductService
from domain.service.stock import StockService
from domain.service.user import DuplicateEmailError, PermissionDeniedError, UserService

__all__ = [
    "AuthService",
    "DashboardService",
    "DuplicateEmailError",
    "DuplicateSkuError",
    "HealthService",
    "OrderService",
    "PermissionDeniedError",
    "ProductService",
    "StockService",
    "UserService",
]
