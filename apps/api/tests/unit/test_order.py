"""Agregado Order e sua maquina de estados."""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.exception import BusinessRuleViolationError, InvariantViolationError
from domain.model.money import Money
from domain.model.order import (
    Customer,
    InvalidStatusTransitionError,
    Order,
    OrderItem,
    OrderStatus,
)


def build_item(*, quantity: int = 2, price: int = 3290) -> OrderItem:
    return OrderItem(
        product_id=uuid4(),
        sku="CAF-500",
        description="Cafe 500g",
        quantity=quantity,
        unit_price=Money(price),
    )


def build_order(*, items: list[OrderItem] | None = None) -> Order:
    return Order.place(
        reference="PED-000001",
        customer=Customer(name="Marina Duarte", email="marina@exemplo.com"),
        # `or` aqui trocaria uma lista vazia pelo padrao e esconderia o caso
        # que o teste de invariante quer exercitar.
        items=[build_item()] if items is None else items,
    )


# -- invariantes ------------------------------------------------------------
def test_pedido_sem_itens_e_recusado() -> None:
    with pytest.raises(InvariantViolationError, match="pelo menos um item"):
        build_order(items=[])


def test_item_com_quantidade_zero_e_recusado() -> None:
    with pytest.raises(InvariantViolationError, match="maior que zero"):
        build_item(quantity=0)


def test_cliente_com_email_invalido_e_recusado() -> None:
    with pytest.raises(InvariantViolationError, match="E-mail invalido"):
        Customer(name="Marina", email="marina-arroba-exemplo")


def test_total_soma_os_subtotais() -> None:
    order = build_order(
        items=[build_item(quantity=2, price=3290), build_item(quantity=1, price=1890)]
    )

    assert order.total == Money(2 * 3290 + 1890)
    assert order.item_count == 3


def test_itens_expostos_sao_imutaveis() -> None:
    order = build_order()

    assert isinstance(order.items, tuple)


# -- maquina de estados -----------------------------------------------------
def test_fluxo_feliz_ate_a_entrega() -> None:
    order = build_order()

    order.confirm()
    order.ship()
    order.deliver()

    assert order.status is OrderStatus.DELIVERED


@pytest.mark.parametrize(
    ("preparar", "acao"),
    [
        (lambda o: None, "ship"),
        (lambda o: None, "deliver"),
        (lambda o: o.confirm(), "deliver"),
    ],
)
def test_transicoes_fora_da_maquina_sao_recusadas(preparar, acao: str) -> None:
    order = build_order()
    preparar(order)

    with pytest.raises(InvalidStatusTransitionError) as exc_info:
        getattr(order, acao)()

    assert "allowed" in exc_info.value.details()


def test_pedido_entregue_e_terminal() -> None:
    order = build_order()
    order.confirm()
    order.ship()
    order.deliver()

    with pytest.raises(InvalidStatusTransitionError):
        order.cancel("arrependimento")


def test_pedido_cancelado_nao_volta_atras() -> None:
    order = build_order()
    order.cancel("Cliente desistiu")

    assert order.status is OrderStatus.CANCELLED
    assert order.cancellation_reason == "Cliente desistiu"

    with pytest.raises(InvalidStatusTransitionError):
        order.confirm()


def test_cancelamento_exige_motivo() -> None:
    order = build_order()

    with pytest.raises(InvariantViolationError, match="motivo"):
        order.cancel("   ")


def test_mudanca_de_status_registra_evento() -> None:
    order = build_order()
    order.pull_events()  # descarta o OrderPlaced

    order.confirm()

    events = order.pull_events()
    assert [event.name for event in events] == ["OrderStatusChanged"]


# -- edicao -----------------------------------------------------------------
def test_itens_podem_ser_trocados_enquanto_pendente() -> None:
    order = build_order()
    novo = build_item(quantity=5)

    order.replace_items([novo])

    assert order.items == (novo,)


def test_itens_nao_mudam_depois_de_confirmado() -> None:
    order = build_order()
    order.confirm()

    with pytest.raises(BusinessRuleViolationError, match="nao podem ser alterados"):
        order.replace_items([build_item()])


def test_troca_por_lista_vazia_e_recusada() -> None:
    order = build_order()

    with pytest.raises(InvariantViolationError, match="pelo menos um item"):
        order.replace_items([])
