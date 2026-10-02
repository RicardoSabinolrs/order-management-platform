"""ProductService com repositorios em memoria."""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.exception import BusinessRuleViolationError, EntityNotFoundError
from domain.schema.page import PageQuery
from domain.schema.product import ProductCreate, ProductUpdate
from domain.service.product import DuplicateSkuError, ProductService
from tests.fakes.unit_of_work import InMemoryDatabase


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def service(database: InMemoryDatabase) -> ProductService:
    return ProductService(database)


def payload(**overrides: object) -> ProductCreate:
    data: dict[str, object] = {
        "sku": "CAF-500",
        "name": "Cafe torrado e moido 500g",
        "description": "Pacote de 500g",
        "price_in_cents": 3290,
    }
    data.update(overrides)
    return ProductCreate.model_validate(data)


async def test_cria_produto_e_registro_de_estoque(
    service: ProductService, database: InMemoryDatabase
) -> None:
    created = await service.create(payload(initial_stock=25))

    assert created.sku == "CAF-500"
    assert database.commits == 1

    # Produto sem registro de estoque quebraria a primeira venda.
    stock = database.stock[created.id]
    assert stock.quantity_on_hand == 25
    assert stock.quantity_available == 25


async def test_produto_sem_estoque_inicial_nasce_zerado(
    service: ProductService, database: InMemoryDatabase
) -> None:
    created = await service.create(payload())

    assert database.stock[created.id].quantity_on_hand == 0


async def test_sku_duplicado_e_recusado(service: ProductService) -> None:
    await service.create(payload())

    with pytest.raises(DuplicateSkuError, match="Ja existe um produto"):
        await service.create(payload(name="Outro nome"))


async def test_sku_duplicado_ignora_caixa_e_espacos(service: ProductService) -> None:
    await service.create(payload())

    with pytest.raises(DuplicateSkuError):
        await service.create(payload(sku="  caf-500  "))


async def test_atualizacao_parcial_mantem_os_demais_campos(service: ProductService) -> None:
    created = await service.create(payload())

    updated = await service.update(created.id, ProductUpdate(price_in_cents=3990))

    assert updated.price_in_cents == 3990
    assert updated.name == created.name
    assert updated.active is True


async def test_desativacao_pelo_update(service: ProductService) -> None:
    created = await service.create(payload())

    updated = await service.update(created.id, ProductUpdate(active=False))

    assert updated.active is False


async def test_busca_por_nome_ou_sku(service: ProductService) -> None:
    await service.create(payload())
    await service.create(payload(sku="CHA-VER-100", name="Cha verde folhas 100g"))

    page = await service.paginate(page_query=PageQuery(), search="cha")

    assert page.total == 1
    assert page.items[0].sku == "CHA-VER-100"


async def test_paginacao_informa_o_total_completo(service: ProductService) -> None:
    for index in range(5):
        await service.create(payload(sku=f"SKU-{index:03d}"))

    page = await service.paginate(page_query=PageQuery(page=1, page_size=2))

    assert len(page.items) == 2
    assert page.total == 5
    assert page.pages == 3


async def test_exclusao_com_estoque_reservado_e_recusada(
    service: ProductService, database: InMemoryDatabase
) -> None:
    created = await service.create(payload(initial_stock=10))
    database.stock[created.id].reserve(4)

    with pytest.raises(BusinessRuleViolationError, match="Desative-o"):
        await service.delete(created.id)


async def test_exclusao_sem_reserva_remove_o_produto(
    service: ProductService, database: InMemoryDatabase
) -> None:
    created = await service.create(payload(initial_stock=10))

    await service.delete(created.id)

    assert created.id not in database.products


async def test_produto_inexistente_devolve_erro_de_dominio(service: ProductService) -> None:
    with pytest.raises(EntityNotFoundError, match="nao encontrado"):
        await service.get(uuid4())
