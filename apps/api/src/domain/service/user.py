"""Cadastro de usuarios, feito por um administrador."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from domain.exception import AuthenticationError, AuthorizationError, BusinessRuleViolationError
from domain.model.user import User
from domain.repository.base import UnitOfWork
from domain.schema.page import Page, PageQuery
from domain.schema.user import UserCreate, UserRead


class DuplicateEmailError(BusinessRuleViolationError):
    """Ja existe um usuario com o e-mail informado."""

    code = "email_ja_cadastrado"


class PermissionDeniedError(AuthorizationError):
    """O usuario autenticado nao tem o papel exigido pela operacao."""

    code = "permissao_negada"


class PasswordHasher(Protocol):
    """Gera o hash de uma senha. Implementado em `security/password.py`."""

    def __call__(self, plain_password: str) -> str: ...


class UserService:
    """Listagem e cadastro de usuarios, restritos a administradores.

    Nao ha auto-cadastro: todo usuario nasce pelas maos de um admin, e o
    primeiro admin e o operador definido na configuracao.
    """

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        *,
        hash_password: PasswordHasher,
    ) -> None:
        self._unit_of_work = unit_of_work_factory
        self._hash_password = hash_password

    async def paginate(self, *, actor_id: str, page_query: PageQuery) -> Page[UserRead]:
        async with self._unit_of_work() as uow:
            await self._require_admin(uow, actor_id)
            users, total = await uow.users.paginate(
                offset=page_query.offset, limit=page_query.page_size
            )
            return Page[UserRead](
                items=[UserRead.from_domain(user) for user in users],
                total=total,
                page=page_query.page,
                page_size=page_query.page_size,
            )

    async def create(self, *, actor_id: str, payload: UserCreate) -> UserRead:
        """Cadastra um usuario.

        Raises:
            PermissionDeniedError: quem pede nao e admin.
            DuplicateEmailError: o e-mail ja pertence a alguem, inclusive ao
                operador da configuracao.
        """
        async with self._unit_of_work() as uow:
            await self._require_admin(uow, actor_id)

            email = payload.email.strip().lower()
            if await uow.users.get_by_email(email) is not None:
                msg = f"Ja existe um usuario com o e-mail {email}."
                raise DuplicateEmailError(msg)

            # O hash so e calculado depois das checagens: Argon2 e caro de
            # proposito, e nao ha por que paga-lo para uma requisicao recusada.
            user = User.create(
                name=payload.name,
                email=email,
                role=payload.role,
                password_hash=self._hash_password(payload.password),
            )
            await uow.users.add(user)
            await uow.commit()
            return UserRead.from_domain(user)

    @staticmethod
    async def _require_admin(uow: UnitOfWork, actor_id: str) -> User:
        # O papel e lido do cadastro, nao do token: uma mudanca de papel vale
        # ja na proxima requisicao, sem esperar o token expirar.
        actor = await uow.users.get(actor_id)
        if actor is None:
            msg = "Sessao invalida."
            raise AuthenticationError(msg)
        if not actor.is_admin:
            msg = "Somente administradores podem gerenciar usuarios."
            raise PermissionDeniedError(msg)
        return actor
