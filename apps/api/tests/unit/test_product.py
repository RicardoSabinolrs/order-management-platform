"""Agregado Product."""

from __future__ import annotations

import pytest

from domain.exception import InvariantViolationError
from domain.model.money import Money
from domain.model.product import Product


def build_product(**overrides: object) -> Product:
    defaults: dict[str, object] = {
        "sku": "caf-500",
        "name": "Cafe torrado e moido 500g",
        "description": "Pacote de 500g",
        "price": Money(3290),
    }
    defaults.update(overrides)
    return Product.create(**defaults)  # type: ignore[arg-type]


def test_sku_e_normalizado_para_maiusculas() -> None:
    assert build_product(sku="  caf-500 ").sku == "CAF-500"


@pytest.mark.parametrize("sku", ["ab", "caf 500", "-CAF", "CAF@500", "A" * 33])
def test_sku_invalido_e_recusado(sku: str) -> None:
    with pytest.raises(InvariantViolationError, match="SKU invalido"):
        build_product(sku=sku)


def test_nome_vazio_e_recusado() -> None:
    with pytest.raises(InvariantViolationError, match="nao pode ser vazio"):
        build_product(name="   ")


def test_criacao_registra_evento() -> None:
    product = build_product()

    events = product.pull_events()

    assert [event.name for event in events] == ["ProductCreated"]


def test_alteracao_de_preco_atualiza_o_carimbo_de_tempo() -> None:
    product = build_product()
    before = product.updated_at

    product.change_price(Money(3990))

    assert product.price == Money(3990)
    assert product.updated_at >= before


def test_desativar_preserva_o_produto() -> None:
    product = build_product()

    product.deactivate()

    assert product.is_active is False
    product.activate()
    assert product.is_active is True
