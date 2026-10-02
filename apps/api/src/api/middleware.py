"""Middlewares HTTP transversais."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from starlette.requests import Request
from starlette.responses import Response

from infra.observability.metrics import (
    REQUEST_DURATION,
    REQUESTS_IN_FLIGHT,
    REQUESTS_TOTAL,
    route_template,
)

REQUEST_ID_HEADER = "X-Request-ID"

type CallNext = Callable[[Request], Awaitable[Response]]


async def correlation_id_middleware(request: Request, call_next: CallNext) -> Response:
    """Propaga um identificador de correlacao por toda a requisicao.

    Entra pelo header quando o cliente ou o gateway ja enviou um, e aparece em
    cada linha de log daquela requisicao. E o que permite reconstruir uma
    chamada inteira no Loki a partir de um unico id.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.unbind_contextvars("request_id", "method", "path")

    response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def metrics_middleware(request: Request, call_next: CallNext) -> Response:
    """Contabiliza contador, histograma e gauge de cada requisicao."""
    method = request.method
    started = time.perf_counter()

    REQUESTS_IN_FLIGHT.labels(method=method).inc()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
    finally:
        REQUESTS_IN_FLIGHT.labels(method=method).dec()
        # O template so existe depois do roteamento, por isso e lido aqui.
        template = route_template(request)
        REQUEST_DURATION.labels(method=method, path=template).observe(time.perf_counter() - started)
        REQUESTS_TOTAL.labels(method=method, path=template, status=str(status)).inc()

    return response
