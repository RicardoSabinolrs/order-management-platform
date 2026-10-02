"""AuthService: login e sessao."""

from __future__ import annotations

import re

import pytest
from pydantic import SecretStr

from domain.exception import AuthenticationError
from domain.model.user import User
from domain.schema.auth import LoginRequest
from domain.service.auth import AuthService
from infra.config.settings import SecuritySettings
from infra.repository.user import SettingsUserRepository
from security.password import hash_password, verify_password
from security.token import TokenService
from tests.fakes.unit_of_work import InMemoryDatabase

SETTINGS = SecuritySettings(
    issuer="api-de-teste",
    operator_email="operador@exemplo.com",
    operator_password=SecretStr("senha-de-teste"),
)


@pytest.fixture(scope="module")
def root_users() -> SettingsUserRepository:
    # Hash Argon2 uma vez so por modulo: e caro de proposito.
    return SettingsUserRepository(SETTINGS)


@pytest.fixture
def database(root_users: SettingsUserRepository) -> InMemoryDatabase:
    return InMemoryDatabase(root_users=root_users)


@pytest.fixture
def service(database: InMemoryDatabase) -> AuthService:
    return AuthService(
        database,
        token_issuer=TokenService(SETTINGS),
        verify_password=verify_password,
    )


async def test_login_valido_emite_token_e_usuario(service: AuthService) -> None:
    response = await service.login(
        LoginRequest(email="operador@exemplo.com", password="senha-de-teste")
    )

    assert response.token_type == "bearer"
    assert response.access_token
    assert response.user.email == "operador@exemplo.com"
    # O operador da configuracao e o admin raiz.
    assert response.user.role == "admin"
    assert response.user.avatar_url == "/avatars/operador.jpg"


async def test_email_e_case_insensitive(service: AuthService) -> None:
    response = await service.login(
        LoginRequest(email="  OPERADOR@exemplo.COM ", password="senha-de-teste")
    )

    assert response.user.email == "operador@exemplo.com"


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("operador@exemplo.com", "senha-errada"),
        ("desconhecido@exemplo.com", "senha-de-teste"),
    ],
)
async def test_credencial_invalida_usa_sempre_a_mesma_mensagem(
    service: AuthService, email: str, password: str
) -> None:
    # Distinguir "usuario nao existe" de "senha errada" entregaria a lista de
    # e-mails validos a quem estivesse sondando.
    with pytest.raises(AuthenticationError, match=re.escape("E-mail ou senha incorretos.")):
        await service.login(LoginRequest(email=email, password=password))


async def test_token_emitido_identifica_o_usuario(service: AuthService) -> None:
    response = await service.login(
        LoginRequest(email="operador@exemplo.com", password="senha-de-teste")
    )

    payload = TokenService(SETTINGS).decode_access_token(response.access_token)
    user = await service.me(payload.sub)

    assert user.email == "operador@exemplo.com"
    assert payload.scopes == ["admin"]


async def test_usuario_cadastrado_no_banco_tambem_faz_login(
    service: AuthService, database: InMemoryDatabase
) -> None:
    user = User.create(
        name="Ana Souza",
        email="ana@exemplo.com",
        role="viewer",
        password_hash=hash_password("senha-da-ana"),
    )
    database.users[user.id] = user

    response = await service.login(LoginRequest(email="ANA@exemplo.com", password="senha-da-ana"))

    assert response.user.id == user.id
    assert response.user.role == "viewer"
    assert response.user.avatar_url is None
    assert (await service.me(user.id)).email == "ana@exemplo.com"


async def test_sessao_com_usuario_inexistente_e_recusada(service: AuthService) -> None:
    with pytest.raises(AuthenticationError, match="Sessao invalida"):
        await service.me("usr_inexistente")


async def test_senha_nunca_e_guardada_em_claro(root_users: SettingsUserRepository) -> None:
    user = await root_users.get_by_email("operador@exemplo.com")

    assert user is not None
    assert "senha-de-teste" not in user.password_hash
    assert user.password_hash.startswith("$argon2")
