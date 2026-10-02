"""Implementacao Postgres do contrato de saude."""

from __future__ import annotations

from sqlalchemy import text

from infra.database.session import Database
from infra.logging.setup import get_logger

_logger = get_logger(__name__)


class PostgresHealthRepository:
    """Verifica se o Postgres responde."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def is_available(self) -> bool:
        """Executa um `SELECT 1`.

        Nunca propaga excecao: o readiness precisa responder "nao estou pronto",
        nao derrubar o processo.
        """
        try:
            async with self._database.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as error:  # noqa: BLE001 - qualquer falha significa indisponivel
            _logger.warning("database_unavailable", error=str(error))
            return False
        return True
