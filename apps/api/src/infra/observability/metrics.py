"""Metricas Prometheus.

Series que alimentam os paineis do Grafana e os alertas: taxa de requisicoes,
latencia por rota e requisicoes em voo.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram
from prometheus_client import generate_latest as _generate_latest
from starlette.requests import Request
from starlette.responses import Response

REGISTRY = CollectorRegistry(auto_describe=True)

REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de requisicoes HTTP recebidas.",
    labelnames=("method", "path", "status"),
    registry=REGISTRY,
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Latencia das requisicoes HTTP, em segundos.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

REQUESTS_IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Requisicoes HTTP em processamento.",
    labelnames=("method",),
    registry=REGISTRY,
)


def render_metrics() -> Response:
    """Resposta no formato de exposicao do Prometheus."""
    return Response(content=_generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def route_template(request: Request) -> str:
    """Rota parametrizada (`/orders/{order_id}`), nunca a URL concreta.

    Usar o caminho concreto criaria uma serie temporal por id - a cardinalidade
    cresceria sem limite e derrubaria o Prometheus.
    """
    route = request.scope.get("route")
    path: str | None = getattr(route, "path", None)
    return path or "__unmatched__"
