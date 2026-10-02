"""Cadastro de usuarios pela fronteira HTTP.

Mesma montagem de `test_api_endpoints`: rota de verdade, repositorios em
memoria. O token vem do login real do admin raiz, entao o caminho completo -
login, bearer, checagem de papel - e exercitado.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.deps import get_unit_of_work_factory
from infra.config.settings import Settings
from tests.fakes.unit_of_work import InMemoryDatabase

NOVO_USUARIO = {
    "name": "Ana Souza",
    "email": "ana@exemplo.com",
    "password": "senha-da-ana",
    "role": "viewer",
}


@pytest.fixture
def database(app: FastAPI) -> InMemoryDatabase:
    return InMemoryDatabase(root_users=app.state.root_users)


@pytest.fixture
async def api(app: FastAPI, database: InMemoryDatabase) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_unit_of_work_factory] = lambda: database
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client
    app.dependency_overrides.clear()


async def login(api: AsyncClient, email: str, password: str) -> dict[str, str]:
    response = await api.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == HTTPStatus.OK, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
async def admin(api: AsyncClient, settings: Settings) -> dict[str, str]:
    return await login(
        api,
        settings.security.operator_email,
        settings.security.operator_password.get_secret_value(),
    )


async def test_login_do_admin_raiz_traz_papel_e_avatar(
    api: AsyncClient, settings: Settings
) -> None:
    response = await api.post(
        "/auth/login",
        json={
            "email": settings.security.operator_email,
            "password": settings.security.operator_password.get_secret_value(),
        },
    )

    user = response.json()["user"]
    assert user["role"] == "admin"
    assert user["avatar_url"] == settings.security.operator_avatar_url
    assert set(user) == {"id", "name", "email", "role", "avatar_url"}


async def test_admin_cadastra_usuario(api: AsyncClient, admin: dict[str, str]) -> None:
    response = await api.post("/users", json=NOVO_USUARIO, headers=admin)

    assert response.status_code == HTTPStatus.CREATED, response.text
    body = response.json()
    assert set(body) == {"id", "name", "email", "role", "avatar_url"}
    assert body["email"] == "ana@exemplo.com"
    assert body["role"] == "viewer"
    assert body["avatar_url"] is None


async def test_usuario_cadastrado_faz_login_e_ve_a_si_mesmo(
    api: AsyncClient, admin: dict[str, str]
) -> None:
    created = (await api.post("/users", json=NOVO_USUARIO, headers=admin)).json()

    headers = await login(api, "ANA@exemplo.com", "senha-da-ana")
    response = await api.get("/auth/me", headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == created


async def test_listagem_paginada_de_usuarios(api: AsyncClient, admin: dict[str, str]) -> None:
    for index in range(3):
        await api.post(
            "/users", json={**NOVO_USUARIO, "email": f"user{index}@exemplo.com"}, headers=admin
        )

    response = await api.get("/users", params={"page": 1, "page_size": 2}, headers=admin)

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert set(body) == {"items", "total", "page", "page_size"}
    assert body["total"] == 4  # os tres cadastrados mais o admin raiz
    assert len(body["items"]) == 2
    assert body["items"][0]["role"] == "admin"


async def test_email_duplicado_devolve_409(api: AsyncClient, admin: dict[str, str]) -> None:
    await api.post("/users", json=NOVO_USUARIO, headers=admin)

    response = await api.post("/users", json=NOVO_USUARIO, headers=admin)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "email_ja_cadastrado"


async def test_email_do_admin_raiz_devolve_409(
    api: AsyncClient, admin: dict[str, str], settings: Settings
) -> None:
    response = await api.post(
        "/users", json={**NOVO_USUARIO, "email": settings.security.operator_email}, headers=admin
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "email_ja_cadastrado"


@pytest.mark.parametrize("role", ["operator", "viewer"])
async def test_nao_admin_recebe_403(api: AsyncClient, admin: dict[str, str], role: str) -> None:
    await api.post("/users", json={**NOVO_USUARIO, "role": role}, headers=admin)
    comum = await login(api, NOVO_USUARIO["email"], NOVO_USUARIO["password"])

    listagem = await api.get("/users", headers=comum)
    cadastro = await api.post(
        "/users", json={**NOVO_USUARIO, "email": "outro@exemplo.com"}, headers=comum
    )

    for response in (listagem, cadastro):
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["code"] == "permissao_negada"


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "x" * 121},
        {"email": "nao-e-email"},
        {"password": "curta"},
        {"role": "superusuario"},
    ],
)
async def test_payload_invalido_devolve_422(
    api: AsyncClient, admin: dict[str, str], overrides: dict[str, str]
) -> None:
    response = await api.post("/users", json={**NOVO_USUARIO, **overrides}, headers=admin)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


async def test_sem_token_devolve_401(api: AsyncClient) -> None:
    listagem = await api.get("/users")
    cadastro = await api.post("/users", json=NOVO_USUARIO)

    for response in (listagem, cadastro):
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["code"] == "unauthenticated"
