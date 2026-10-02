"""Repositorios de usuarios.

Os usuarios vem de duas fontes: o administrador raiz, definido por variavel de
ambiente, e os cadastrados no banco. O raiz existe sem estar na tabela para que
uma instalacao nova ja tenha quem cadastre os demais - e para que ninguem perca
o acesso por apagar uma linha. `CompositeUserRepository` junta as duas fontes
atras da porta `UserRepository`, e o resto da aplicacao nao sabe que sao duas.
"""

from __future__ import annotations

from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.model.user import Role, User
from domain.repository.user import UserRepository
from infra.config.settings import SecuritySettings
from infra.database.model.user import UserTable
from security.password import hash_password

OPERATOR_ID = "usr_operator"


class SettingsUserRepository:
    """O administrador raiz, montado a partir das settings."""

    def __init__(self, settings: SecuritySettings) -> None:
        self._user = User(
            OPERATOR_ID,
            name=settings.operator_name,
            email=settings.operator_email,
            role="admin",
            # O hash e calculado na subida: a senha em claro nunca fica
            # guardada em memoria por mais tempo que o necessario.
            password_hash=hash_password(settings.operator_password.get_secret_value()),
            avatar_url=settings.operator_avatar_url,
        )

    @property
    def user(self) -> User:
        return self._user

    async def get(self, user_id: str) -> User | None:
        return self._user if user_id == self._user.id else None

    async def get_by_email(self, email: str) -> User | None:
        return self._user if email.strip().lower() == self._user.email else None


def _to_domain(row: UserTable) -> User:
    return User(
        row.id,
        name=row.name,
        email=row.email,
        # A check constraint do banco garante que o valor e um dos papeis.
        role=cast(Role, row.role),
        password_hash=row.password_hash,
        avatar_url=row.avatar_url,
        created_at=row.created_at,
    )


class SqlAlchemyUserRepository:
    """Traduz entre `User` e a tabela `users`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: str) -> User | None:
        row = await self._session.get(UserTable, user_id)
        return None if row is None else _to_domain(row)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(UserTable).where(UserTable.email == email.strip().lower())
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else _to_domain(row)

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        total_statement = select(func.count()).select_from(UserTable)
        total = (await self._session.execute(total_statement)).scalar_one()
        statement = (
            select(UserTable).order_by(UserTable.name, UserTable.email).offset(offset).limit(limit)
        )
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_domain(row) for row in rows], total

    async def add(self, user: User) -> None:
        self._session.add(
            UserTable(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                password_hash=user.password_hash,
                avatar_url=user.avatar_url,
                created_at=user.created_at,
            )
        )


class CompositeUserRepository:
    """Administrador raiz + usuarios do banco, como um repositorio so.

    O raiz e consultado primeiro: login e `/auth/me` dele nao tocam o banco, e
    o e-mail dele aparece como ocupado para quem tentar cadastra-lo de novo.
    Na listagem, ele ocupa sempre a primeira posicao.
    """

    def __init__(self, root: SettingsUserRepository, stored: UserRepository) -> None:
        self._root = root
        self._stored = stored

    async def get(self, user_id: str) -> User | None:
        return await self._root.get(user_id) or await self._stored.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._root.get_by_email(email) or await self._stored.get_by_email(email)

    async def paginate(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        # O raiz e o registro de indice 0; os do banco vem deslocados de um.
        if offset == 0:
            stored, total = await self._stored.paginate(offset=0, limit=limit - 1)
            return [self._root.user, *stored], total + 1
        stored, total = await self._stored.paginate(offset=offset - 1, limit=limit)
        return stored, total + 1

    async def add(self, user: User) -> None:
        await self._stored.add(user)
