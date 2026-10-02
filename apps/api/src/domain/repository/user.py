"""Porta de persistencia de usuarios."""

from __future__ import annotations

from typing import Protocol

from domain.model.user import User


class UserRepository(Protocol):
    async def get(self, user_id: str) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        """Pagina de usuarios e o total cadastrado."""
        ...

    async def add(self, user: User) -> None: ...
