"""Service das sondas de saude.

Toda a decisao mora aqui: o endpoint apenas repassa o resultado. Quando uma
dependencia cai, o service levanta `DependencyUnavailableError` - traduzir isso
para 503 e problema da camada `api`, nao deste modulo.
"""

from __future__ import annotations

from domain.exception import DependencyUnavailableError
from domain.repository.health import HealthRepository
from domain.schema.health import DependencyStatusSchema, LivenessSchema, ReadinessSchema


class HealthService:
    """Responde pelo estado do servico e de suas dependencias."""

    def __init__(
        self,
        health_repository: HealthRepository,
        *,
        service_name: str,
        version: str,
    ) -> None:
        self._health_repository = health_repository
        self._service_name = service_name
        self._version = version

    def liveness(self) -> LivenessSchema:
        """O processo esta vivo. Nao consulta dependencia alguma.

        Liveness que depende do banco faz o Kubernetes reiniciar pods saudaveis
        quando o banco oscila - exatamente o oposto do que se quer.
        """
        return LivenessSchema(service=self._service_name, version=self._version)

    async def readiness(self) -> ReadinessSchema:
        """O servico pode receber trafego.

        Raises:
            DependencyUnavailableError: alguma dependencia nao respondeu.
        """
        dependencies = [
            DependencyStatusSchema(
                name="postgres",
                healthy=await self._health_repository.is_available(),
            ),
        ]

        unhealthy = [dependency.name for dependency in dependencies if not dependency.healthy]
        if unhealthy:
            raise DependencyUnavailableError(
                f"Dependencias indisponiveis: {', '.join(unhealthy)}.",
                dependencies=[dependency.model_dump() for dependency in dependencies],
            )

        return ReadinessSchema(dependencies=dependencies)
