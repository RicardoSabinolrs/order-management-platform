"""Sondas de saude.

Ficam fora do prefixo versionado de proposito: kubelet, load balancer e
Prometheus consomem caminhos fixos, que nao devem mudar quando o contrato de
negocio ganha uma nova versao.

`/health/live`  - o processo esta vivo; falhar aqui reinicia o pod.
`/health/ready` - as dependencias respondem; falhar aqui tira o pod do
                  balanceador sem reinicia-lo.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from api.deps import HealthServiceDep
from domain.schema.health import LivenessSchema, ReadinessSchema

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    response_model=LivenessSchema,
    summary="Liveness probe",
)
async def liveness(service: HealthServiceDep) -> LivenessSchema:
    return service.liveness()


@router.get(
    "/ready",
    response_model=ReadinessSchema,
    summary="Readiness probe",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Alguma dependencia nao respondeu.",
        },
    },
)
async def readiness(service: HealthServiceDep) -> ReadinessSchema:
    return await service.readiness()
