"""Usuario da aplicacao."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from domain.exception import InvariantViolationError
from domain.model.base import Entity

Role = Literal["admin", "operator", "viewer"]

ROLES: tuple[Role, ...] = ("admin", "operator", "viewer")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_NAME_LENGTH = 120


class User(Entity[str]):
    """Quem opera a plataforma.

    Guarda o hash da senha, nunca a senha: um vazamento do banco nao pode
    entregar as credenciais.
    """

    __slots__ = ("_avatar_url", "_created_at", "_email", "_name", "_password_hash", "_role")

    def __init__(
        self,
        user_id: str,
        *,
        name: str,
        email: str,
        role: Role,
        password_hash: str,
        avatar_url: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(user_id)
        self._name = self._validate_name(name)
        self._email = self._validate_email(email)
        self._role = role
        self._password_hash = password_hash
        self._avatar_url = avatar_url
        self._created_at = created_at or datetime.now(UTC)

    # -- fabrica ------------------------------------------------------------
    @classmethod
    def create(
        cls,
        *,
        name: str,
        email: str,
        role: Role,
        password_hash: str,
        avatar_url: str | None = None,
    ) -> User:
        """Cria um usuario novo, com id gerado pela aplicacao."""
        return cls(
            str(uuid4()),
            name=name,
            email=email,
            role=role,
            password_hash=password_hash,
            avatar_url=avatar_url,
        )

    # -- validacoes ---------------------------------------------------------
    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            msg = "O nome do usuario nao pode ser vazio."
            raise InvariantViolationError(msg)
        if len(normalized) > MAX_NAME_LENGTH:
            msg = f"O nome do usuario excede {MAX_NAME_LENGTH} caracteres."
            raise InvariantViolationError(msg)
        return normalized

    @staticmethod
    def _validate_email(email: str) -> str:
        # Minusculo sempre: o e-mail e a chave do login, e "Ana@" e "ana@" sao
        # a mesma pessoa.
        normalized = email.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            msg = f"E-mail invalido: '{email}'."
            raise InvariantViolationError(msg)
        return normalized

    # -- estado -------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def role(self) -> Role:
        return self._role

    @property
    def is_admin(self) -> bool:
        return self._role == "admin"

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def avatar_url(self) -> str | None:
        return self._avatar_url

    @property
    def created_at(self) -> datetime:
        return self._created_at
