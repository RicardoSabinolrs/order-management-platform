"""Fabrica e ponto de entrada da aplicacao.

    uv run uvicorn main:app --reload

Esta e a camada mais externa: monta configuracao, adapters e rotas. Nada em
`domain/` sabe que este modulo existe.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.errors import register_exception_handlers
from api.metrics import metrics_endpoint
from api.middleware import correlation_id_middleware, metrics_middleware
from api.router import infrastructure_router, v1_router
from infra.config.settings import Settings, get_settings
from infra.database.session import Database
from infra.logging.setup import configure_logging, get_logger
from infra.repository.user import SettingsUserRepository
from security.token import TokenService

_logger = get_logger(__name__)

OPENAPI_TAGS = [
    {"name": "autenticacao", "description": "Login e sessao do usuario."},
    {"name": "usuarios", "description": "Cadastro de usuarios, restrito a administradores."},
    {"name": "painel", "description": "Visao consolidada de pedidos e estoque."},
    {"name": "produtos", "description": "Catalogo: CRUD de produtos."},
    {"name": "estoque", "description": "Saldos, entradas e ajustes de inventario."},
    {"name": "pedidos", "description": "Pedidos de venda e seu ciclo de vida."},
    {"name": "health", "description": "Sondas de liveness e readiness."},
]


def _build_lifespan(
    settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Cria os recursos de longa duracao na subida e os libera na descida."""
        database = Database(settings.database)

        app.state.settings = settings
        app.state.database = database
        app.state.token_service = TokenService(settings.security)

        _logger.info(
            "application_started",
            env=settings.env,
            version=settings.version,
            database_host=settings.database.host,
        )
        try:
            yield
        finally:
            await database.dispose()
            _logger.info("application_stopped")

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Constroi a aplicacao.

    Recebe `settings` para que os testes montem uma instancia isolada, sem
    depender do ambiente da maquina.
    """
    settings = settings or get_settings()

    configure_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        service_name=settings.observability.service_name,
    )

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        debug=settings.debug,
        openapi_tags=OPENAPI_TAGS,
        # Schema e docs ficam fora do ar em producao: o contrato interno nao
        # precisa estar publicado na internet.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=_build_lifespan(settings),
    )
    # Disponivel antes do lifespan para que `create_app` ja sirva aos testes
    # que nao sobem o ciclo completo.
    app.state.settings = settings
    app.state.token_service = TokenService(settings.security)
    # Montado so aqui, e nao tambem no lifespan: calcular o hash Argon2 da
    # senha do admin raiz e caro, e uma vez por processo basta.
    app.state.root_users = SettingsUserRepository(settings.security)

    # A ordem de registro e a ordem de execucao: correlacao primeiro, para que
    # tudo que vier depois ja logue com o request_id.
    app.add_middleware(BaseHTTPMiddleware, dispatch=correlation_id_middleware)
    if settings.observability.metrics_enabled:
        app.add_middleware(BaseHTTPMiddleware, dispatch=metrics_middleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
        )

    register_exception_handlers(app)

    app.include_router(infrastructure_router)
    app.include_router(v1_router, prefix=settings.api_prefix)

    if settings.observability.metrics_enabled:
        app.add_route(
            settings.observability.metrics_path,
            metrics_endpoint,
            methods=["GET"],
            include_in_schema=False,
        )

    return app


app = create_app()
