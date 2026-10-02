"""Endpoint de exposicao das metricas.

Rota Starlette pura, nao rota FastAPI: o corpo e texto no formato do
Prometheus, sem schema, sem validacao e fora do OpenAPI.
"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from infra.observability.metrics import render_metrics


async def metrics_endpoint(_request: Request) -> Response:
    """Serie temporal acumulada do processo, no formato de exposicao."""
    return render_metrics()
