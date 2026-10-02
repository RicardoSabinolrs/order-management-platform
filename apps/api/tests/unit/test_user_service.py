"""UserService com repositorios em memoria."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from domain.exception import AuthenticationError
from domain.model.user import Role, User
from domain.schema.page import PageQuery
from domain.schema.user import UserCreate
from domain.service.user import DuplicateEmailError, PermissionDeniedError, UserService
from infra.config.settings import SecuritySettings
from infra.repository.user import OPERATOR_ID, SettingsUserRepository
from security.password import hash_password, verify_password
from tests.fakes.unit_of_work import InMemoryDatabase

SETTINGS = SecuritySettings(
    operator_name="Admin Raiz",
    operator_email="admin@exemplo.com",
    operator_password=SecretStr("senha-do-admin"),
)


@pytest.fixture(scope="module")
def root_users() -> SettingsUserRepository:
    return SettingsUserRepository(SETTINGS)


@pytest.fixture
def database(root_users: SettingsUserRepository) -> InMemoryDatabase:
    return InMemoryDatabase(root_users=root_users)


@pytest.fixture
def service(database: InMemoryDatabase) -> UserService:
    return UserService(database, hash_password=hash_password)


def payload(**overrides: object) -> UserCreate:
    data: dict[str, object] = {
        "name": "Ana Souza",
        "email": "ana@exemplo.com",
        "password": "senha-da-ana",
        "role": "operator",
    }
    data.update(overrides)
    return UserCreate.model_validate(data)


def cadastrar(database: InMemoryDatabase, *, email: str, role: Role, name: str = "Fulano") -> User:
    user = User.create(name=name, email=email, role=role, password_hash="hash-qualquer")
    database.users[user.id] = user
    return user


async def test_admin_cadastra_usuario(service: UserService, database: InMemoryDatabase) -> None:
    created = await service.create(actor_id=OPERATOR_ID, payload=payload())

    assert created.email == "ana@exemplo.com"
    assert created.role == "operator"
    assert created.avatar_url is None
    assert database.commits == 1

    stored = database.users[created.id]
    assert stored.password_hash.startswith("$argon2")
    assert verify_password("senha-da-ana", stored.password_hash)


async def test_email_e_gravado_minusculo(service: UserService) -> None:
    created = await service.create(actor_id=OPERATOR_ID, payload=payload(email="Ana@Exemplo.COM"))

    assert created.email == "ana@exemplo.com"


async def test_email_duplicado_e_recusado(service: UserService, database: InMemoryDatabase) -> None:
    await service.create(actor_id=OPERATOR_ID, payload=payload())

    with pytest.raises(DuplicateEmailError) as error:
        await service.create(actor_id=OPERATOR_ID, payload=payload(email="ANA@exemplo.com"))

    assert error.value.code == "email_ja_cadastrado"
    assert len(database.users) == 1


async def test_email_do_admin_raiz_nao_pode_ser_cadastrado(
    service: UserService, database: InMemoryDatabase
) -> None:
    # O raiz nao esta na tabela, mas o e-mail dele conta como ocupado.
    with pytest.raises(DuplicateEmailError):
        await service.create(actor_id=OPERATOR_ID, payload=payload(email="admin@exemplo.com"))

    assert database.users == {}


@pytest.mark.parametrize("role", ["operator", "viewer"])
async def test_nao_admin_nao_cadastra(
    service: UserService, database: InMemoryDatabase, role: Role
) -> None:
    actor = cadastrar(database, email="comum@exemplo.com", role=role)

    with pytest.raises(PermissionDeniedError) as error:
        await service.create(actor_id=actor.id, payload=payload())

    assert error.value.code == "permissao_negada"
    assert database.commits == 0


async def test_nao_admin_nao_lista(service: UserService, database: InMemoryDatabase) -> None:
    actor = cadastrar(database, email="comum@exemplo.com", role="viewer")

    with pytest.raises(PermissionDeniedError):
        await service.paginate(actor_id=actor.id, page_query=PageQuery())


async def test_admin_cadastrado_no_banco_tambem_cadastra(
    service: UserService, database: InMemoryDatabase
) -> None:
    actor = cadastrar(database, email="outro-admin@exemplo.com", role="admin")

    created = await service.create(actor_id=actor.id, payload=payload())

    assert created.id in database.users


async def test_sessao_de_usuario_inexistente_e_recusada(service: UserService) -> None:
    with pytest.raises(AuthenticationError):
        await service.create(actor_id="usr_inexistente", payload=payload())


async def test_listagem_traz_o_admin_raiz_primeiro(
    service: UserService, database: InMemoryDatabase
) -> None:
    cadastrar(database, email="bruno@exemplo.com", role="viewer", name="Bruno")
    cadastrar(database, email="carla@exemplo.com", role="operator", name="Carla")

    page = await service.paginate(actor_id=OPERATOR_ID, page_query=PageQuery())

    assert page.total == 3
    assert [user.email for user in page.items] == [
        "admin@exemplo.com",
        "bruno@exemplo.com",
        "carla@exemplo.com",
    ]
    assert page.items[0].role == "admin"
    assert page.items[0].avatar_url == "/avatars/operador.jpg"


async def test_paginacao_desloca_o_banco_pelo_admin_raiz(
    service: UserService, database: InMemoryDatabase
) -> None:
    for name in ("Bruno", "Carla", "Davi"):
        cadastrar(database, email=f"{name.lower()}@exemplo.com", role="viewer", name=name)

    primeira = await service.paginate(
        actor_id=OPERATOR_ID, page_query=PageQuery(page=1, page_size=2)
    )
    segunda = await service.paginate(
        actor_id=OPERATOR_ID, page_query=PageQuery(page=2, page_size=2)
    )

    assert [user.name for user in primeira.items] == ["Admin Raiz", "Bruno"]
    assert [user.name for user in segunda.items] == ["Carla", "Davi"]
    assert primeira.total == segunda.total == 4
