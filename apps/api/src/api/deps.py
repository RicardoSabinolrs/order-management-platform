"""Montagem das dependencias da camada HTTP.

Aqui os objetos concretos sao ligados uns aos outros. O endpoint declara apenas
o service de que precisa; quem sabe que existe Postgres do outro lado e este
modulo, nao a rota.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Query, Request

from domain.repository.base import UnitOfWork
from domain.schema.page import PageQuery
from domain.service.auth import AuthService
from domain.service.dashboard import DashboardService
from domain.service.health import HealthService
from domain.service.order import OrderService
from domain.service.product import ProductService
from domain.service.stock import StockService
from domain.service.user import UserService
from infra.config.settings import Settings
from infra.database.session import Database
from infra.database.unit_of_work import SqlAlchemyUnitOfWork
from infra.repository.health import PostgresHealthRepository
from infra.repository.user import SettingsUserRepository
from security.dependencies import get_token_service
from security.password import hash_password, verify_password
from security.token import TokenService


def get_settings(request: Request) -> Settings:
    """Configuracao resolvida no start da aplicacao."""
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    """Engine/pool criado no lifespan."""
    database: Database = request.app.state.database
    return database


def get_root_users(request: Request) -> SettingsUserRepository:
    """Administrador raiz, montado uma vez em `create_app`."""
    root_users: SettingsUserRepository = request.app.state.root_users
    return root_users


SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
RootUsersDep = Annotated[SettingsUserRepository, Depends(get_root_users)]


def get_unit_of_work_factory(
    database: DatabaseDep, root_users: RootUsersDep
) -> Callable[[], UnitOfWork]:
    """Fabrica de transacoes.

    Os services recebem a fabrica, nao uma instancia: cada operacao abre a sua
    propria transacao, e uma requisicao com duas operacoes nao acaba com as
    duas presas no mesmo commit.
    """
    return lambda: SqlAlchemyUnitOfWork(database.session_factory, root_users=root_users)


UnitOfWorkFactoryDep = Annotated[Callable[[], UnitOfWork], Depends(get_unit_of_work_factory)]


def get_page_query(
    page: Annotated[int, Query(ge=1, description="Pagina, comecando em 1.")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Itens por pagina.")] = 20,
) -> PageQuery:
    return PageQuery(page=page, page_size=page_size)


PageQueryDep = Annotated[PageQuery, Depends(get_page_query)]


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
def get_health_service(database: DatabaseDep, settings: SettingsDep) -> HealthService:
    return HealthService(
        PostgresHealthRepository(database),
        service_name=settings.observability.service_name,
        version=settings.version,
    )


def get_auth_service(
    uow_factory: UnitOfWorkFactoryDep,
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    return AuthService(uow_factory, token_issuer=token_service, verify_password=verify_password)


def get_user_service(uow_factory: UnitOfWorkFactoryDep) -> UserService:
    return UserService(uow_factory, hash_password=hash_password)


def get_product_service(uow_factory: UnitOfWorkFactoryDep) -> ProductService:
    return ProductService(uow_factory)


def get_stock_service(uow_factory: UnitOfWorkFactoryDep) -> StockService:
    return StockService(uow_factory)


def get_order_service(uow_factory: UnitOfWorkFactoryDep) -> OrderService:
    return OrderService(uow_factory)


def get_dashboard_service(uow_factory: UnitOfWorkFactoryDep) -> DashboardService:
    return DashboardService(uow_factory)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
StockServiceDep = Annotated[StockService, Depends(get_stock_service)]
OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
