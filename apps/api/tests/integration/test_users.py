"""Usuarios contra o Postgres real: mapeamento, indice unico e login."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from http import HTTPStatus

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from domain.model.user import User
from infra.config.settings import Settings
from infra.database.session import Database
from infra.database.unit_of_work import SqlAlchemyUnitOfWork
from main import create_app

pytestmark = pytest.mark.integration

type UnitOfWorkFactory = Callable[[], SqlAlchemyUnitOfWork]


def novo_usuario(email: str = "ana@exemplo.com") -> User:
    return User.create(name="Ana Souza", email=email, role="viewer", password_hash="hash")


async def test_usuario_gravado_volta_identico(unit_of_work_factory: UnitOfWorkFactory) -> None:
    user = novo_usuario()

    async with unit_of_work_factory() as uow:
        await uow.users.add(user)
        await uow.commit()

    async with unit_of_work_factory() as uow:
        loaded = await uow.users.get(user.id)
        by_email = await uow.users.get_by_email("ANA@exemplo.com")

    assert loaded is not None
    assert loaded.email == "ana@exemplo.com"
    assert loaded.role == "viewer"
    assert loaded.avatar_url is None
    assert by_email == loaded


async def test_indice_unico_barra_email_repetido(unit_of_work_factory: UnitOfWorkFactory) -> None:
    async with unit_of_work_factory() as uow:
        await uow.users.add(novo_usuario())
        await uow.commit()

    # Mesmo que o service deixasse passar, o banco recusa.
    with pytest.raises(IntegrityError):
        async with unit_of_work_factory() as uow:
            await uow.users.add(novo_usuario())
            await uow.commit()


async def test_listagem_conta_o_total(unit_of_work_factory: UnitOfWorkFactory) -> None:
    async with unit_of_work_factory() as uow:
        for index in range(3):
            await uow.users.add(novo_usuario(f"user{index}@exemplo.com"))
        await uow.commit()

    async with unit_of_work_factory() as uow:
        items, total = await uow.users.paginate(offset=0, limit=2)

    assert total == 3
    assert len(items) == 2


@pytest.fixture
async def api(settings: Settings, database: Database) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            yield client


async def test_cadastro_e_login_pela_api(api: AsyncClient, settings: Settings) -> None:
    login = await api.post(
        "/auth/login",
        json={
            "email": settings.security.operator_email,
            "password": settings.security.operator_password.get_secret_value(),
        },
    )
    admin = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = await api.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@exemplo.com",
            "password": "senha-da-ana",
            "role": "admin",
        },
        headers=admin,
    )
    assert created.status_code == HTTPStatus.CREATED, created.text

    response = await api.post(
        "/auth/login", json={"email": "ana@exemplo.com", "password": "senha-da-ana"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["user"] == created.json()

    listagem = await api.get("/users", headers=admin)
    assert listagem.json()["total"] == 2
