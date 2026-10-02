"""Logging estruturado.

Em producao, JSON de uma linha por evento - o formato que o Promtail coleta e o
Loki indexa. Em local, saida colorida e legivel.
"""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog

_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


def configure_logging(
    *,
    level: str = "INFO",
    log_format: Literal["console", "json"] = "console",
    service_name: str = "order-management-api",
) -> None:
    """Configura o structlog e redireciona o logging da stdlib para ele."""
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if log_format == "json"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
        )
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)

    # O uvicorn traz handlers proprios: sem isso cada linha sairia duas vezes,
    # uma delas fora do formato estruturado.
    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Logger estruturado para o modulo indicado."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
