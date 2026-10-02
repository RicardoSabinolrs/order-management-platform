"""Metricas e instrumentacao."""

from infra.observability.metrics import (
    REGISTRY,
    REQUEST_DURATION,
    REQUESTS_IN_FLIGHT,
    REQUESTS_TOTAL,
    render_metrics,
    route_template,
)

__all__ = [
    "REGISTRY",
    "REQUESTS_IN_FLIGHT",
    "REQUESTS_TOTAL",
    "REQUEST_DURATION",
    "render_metrics",
    "route_template",
]
