"""Cadastro de usuarios, restrito a administradores."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.deps import PageQueryDep, UserServiceDep
from domain.schema.page import Page
from domain.schema.user import UserCreate, UserRead
from security.dependencies import CurrentSubjectDep

router = APIRouter(
    prefix="/users",
    tags=["usuarios"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token ausente ou invalido."},
        status.HTTP_403_FORBIDDEN: {"description": "O usuario autenticado nao e admin."},
    },
)


@router.get("", response_model=Page[UserRead], summary="Lista os usuarios")
async def list_users(
    subject: CurrentSubjectDep, service: UserServiceDep, page_query: PageQueryDep
) -> Page[UserRead]:
    return await service.paginate(actor_id=subject, page_query=page_query)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um usuario",
    description="Nao ha auto-cadastro: so um admin cria usuarios. E-mail repetido devolve 409.",
)
async def create_user(
    payload: UserCreate, subject: CurrentSubjectDep, service: UserServiceDep
) -> UserRead:
    return await service.create(actor_id=subject, payload=payload)
