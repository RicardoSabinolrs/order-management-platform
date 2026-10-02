"""Fixtures compartilhadas da suite."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from infra.config.settings import Environment, Settings
from main import create_app


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Settings isoladas do ambiente da maquina."""
    return Settings(env=Environment.TEST, debug=True, log_level="WARNING")


@pytest.fixture
def app(settings: Settings) -> Iterator[FastAPI]:
    yield create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP que fala direto com a app ASGI, sem porta de rede.

    O `LifespanManager` executa startup e shutdown de verdade, entao os testes
    exercitam a mesma montagem de dependencias que roda em producao. Criar o
    engine nao abre conexao, logo isto nao exige Postgres no ar.
    """
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
