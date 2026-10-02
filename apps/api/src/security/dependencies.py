"""Dependencias de autenticacao da camada HTTP.

Enquanto nao existe um contexto de usuarios, estas dependencias validam o token
e expoem as claims. Quando o modelo de usuario entrar, `get_current_subject`
passa a carregar o usuario pelo repositorio.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.exception import AuthenticationError, AuthorizationError
from domain.schema.token import TokenPayloadSchema
from security.token import TokenService

# auto_error=False: o erro 401 e montado pelos nossos handlers, em
# problem+json, como todo o resto da API.
bearer_scheme = HTTPBearer(auto_error=False, description="Access token JWT")


def get_token_service(request: Request) -> TokenService:
    """Service de tokens montado no lifespan."""
    token_service: TokenService = request.app.state.token_service
    return token_service


async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenPayloadSchema:
    """Claims do token da requisicao."""
    if credentials is None:
        raise AuthenticationError("Credencial ausente.")
    return token_service.decode_access_token(credentials.credentials)


async def get_current_subject(
    payload: Annotated[TokenPayloadSchema, Depends(get_token_payload)],
) -> str:
    """Identificador do dono do token."""
    return payload.sub


def require_scopes(*required: str) -> object:
    """Constroi uma dependencia que exige os escopos informados.

    @router.get("/orders", dependencies=[Depends(require_scopes("orders:read"))])
    """

    async def dependency(
        payload: Annotated[TokenPayloadSchema, Depends(get_token_payload)],
    ) -> None:
        missing = set(required) - set(payload.scopes)
        if missing:
            raise AuthorizationError(f"Escopos necessarios: {', '.join(sorted(missing))}.")

    return Depends(dependency)


TokenPayloadDep = Annotated[TokenPayloadSchema, Depends(get_token_payload)]
CurrentSubjectDep = Annotated[str, Depends(get_current_subject)]
