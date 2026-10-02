"""Autenticacao de usuarios."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from domain.exception import AuthenticationError
from domain.repository.base import UnitOfWork
from domain.schema.auth import LoginRequest, LoginResponse
from domain.schema.token import TokenSchema
from domain.schema.user import UserRead


class TokenIssuer(Protocol):
    """Emite access tokens. Implementado em `security/token.py`."""

    def create_access_token(
        self, subject: str, *, scopes: list[str] | None = None
    ) -> TokenSchema: ...


class PasswordVerifier(Protocol):
    """Compara senha e hash. Implementado em `security/password.py`."""

    def __call__(self, plain_password: str, hashed_password: str) -> bool: ...


class AuthService:
    """Valida credenciais e emite a sessao."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        *,
        token_issuer: TokenIssuer,
        verify_password: PasswordVerifier,
    ) -> None:
        self._unit_of_work = unit_of_work_factory
        self._tokens = token_issuer
        self._verify_password = verify_password

    async def login(self, payload: LoginRequest) -> LoginResponse:
        """Autentica e emite o access token.

        Raises:
            AuthenticationError: e-mail desconhecido ou senha incorreta.
        """
        async with self._unit_of_work() as uow:
            user = await uow.users.get_by_email(payload.email)

        # A mesma mensagem nos dois casos: distinguir "usuario nao existe" de
        # "senha errada" entrega a lista de e-mails validos a quem sonda.
        if user is None or not self._verify_password(payload.password, user.password_hash):
            msg = "E-mail ou senha incorretos."
            raise AuthenticationError(msg)

        token = self._tokens.create_access_token(user.id, scopes=[user.role])
        return LoginResponse(
            access_token=token.access_token,
            expires_in=token.expires_in,
            user=UserRead.from_domain(user),
        )

    async def me(self, subject: str) -> UserRead:
        """Usuario dono do token da requisicao."""
        async with self._unit_of_work() as uow:
            user = await uow.users.get(subject)
        if user is None:
            msg = "Sessao invalida."
            raise AuthenticationError(msg)
        return UserRead.from_domain(user)
