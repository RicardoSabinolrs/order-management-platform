"""Schemas das sondas de saude."""

from __future__ import annotations

from typing import Literal

from domain.schema.base import BaseSchema


class DependencyStatusSchema(BaseSchema):
    """Estado de uma dependencia externa."""

    name: str
    healthy: bool


class LivenessSchema(BaseSchema):
    """Resposta do liveness probe."""

    status: Literal["alive"] = "alive"
    service: str
    version: str


class ReadinessSchema(BaseSchema):
    """Resposta do readiness probe."""

    status: Literal["ready"] = "ready"
    dependencies: list[DependencyStatusSchema]
