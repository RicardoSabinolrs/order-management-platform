"""Engine e fabrica de sessoes do SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infra.config.settings import DatabaseSettings


class Database:
    """Ciclo de vida do engine e das sessoes.

    Instanciada uma vez no lifespan da aplicacao e guardada em `app.state`.
    """

    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings
        self._engine: AsyncEngine = create_async_engine(
            settings.dsn,
            echo=settings.echo,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_pre_ping=settings.pool_pre_ping,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Sessao de leitura, sem transacao explicita de escrita."""
        async with self._session_factory() as session:
            yield session

    async def dispose(self) -> None:
        """Fecha o pool de conexoes."""
        await self._engine.dispose()
