"""Autenticacao de usuarios."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.deps import AuthServiceDep
from domain.schema.auth import LoginRequest, LoginResponse
from domain.schema.user import UserRead
from security.dependencies import CurrentSubjectDep

router = APIRouter(prefix="/auth", tags=["autenticacao"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Autentica um usuario",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Credencial invalida."}},
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> LoginResponse:
    return await service.login(payload)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Usuario da sessao atual",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token ausente ou invalido."}},
)
async def me(subject: CurrentSubjectDep, service: AuthServiceDep) -> UserRead:
    return await service.me(subject)
