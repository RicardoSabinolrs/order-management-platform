"""Agregado StockItem: o coracao do controle de estoque."""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.exception import BusinessRuleViolationError, InvariantViolationError
from domain.model.stock import InsufficientStockError, StockItem


def build_stock(*, on_hand: int = 0, reserved: int = 0) -> StockItem:
    return StockItem(uuid4(), sku="CAF-500", quantity_on_hand=on_hand, quantity_reserved=reserved)


def test_disponivel_e_o_saldo_menos_o_reservado() -> None:
    stock = build_stock(on_hand=10, reserved=4)

    assert stock.quantity_available == 6


def test_entrada_aumenta_o_saldo() -> None:
    stock = build_stock(on_hand=5)

    stock.receive(10)

    assert stock.quantity_on_hand == 15
    assert stock.quantity_available == 15


@pytest.mark.parametrize("quantity", [0, -3])
def test_movimentacao_precisa_ser_positiva(quantity: int) -> None:
    stock = build_stock(on_hand=5)

    with pytest.raises(InvariantViolationError, match="maior que zero"):
        stock.receive(quantity)


def test_reserva_reduz_o_disponivel_sem_mexer_no_saldo_fisico() -> None:
    stock = build_stock(on_hand=10)

    stock.reserve(3)

    assert stock.quantity_on_hand == 10
    assert stock.quantity_reserved == 3
    assert stock.quantity_available == 7


def test_reserva_acima_do_disponivel_e_recusada() -> None:
    stock = build_stock(on_hand=10, reserved=8)

    with pytest.raises(InsufficientStockError) as exc_info:
        stock.reserve(3)

    error = exc_info.value
    assert error.requested == 3
    assert error.available == 2
    assert error.details() == {"sku": "CAF-500", "requested": 3, "available": 2}


def test_duas_reservas_nao_vendem_a_mesma_unidade() -> None:
    stock = build_stock(on_hand=5)

    stock.reserve(3)
    with pytest.raises(InsufficientStockError):
        stock.reserve(3)

    assert stock.quantity_reserved == 3


def test_liberacao_devolve_ao_disponivel() -> None:
    stock = build_stock(on_hand=10, reserved=4)

    stock.release(4)

    assert stock.quantity_reserved == 0
    assert stock.quantity_available == 10


def test_nao_libera_mais_do_que_o_reservado() -> None:
    stock = build_stock(on_hand=10, reserved=2)

    with pytest.raises(BusinessRuleViolationError, match="para liberar"):
        stock.release(3)


def test_envio_baixa_saldo_e_reserva() -> None:
    stock = build_stock(on_hand=10, reserved=4)

    stock.ship(4)

    assert stock.quantity_on_hand == 6
    assert stock.quantity_reserved == 0


def test_nao_envia_o_que_nao_foi_reservado() -> None:
    stock = build_stock(on_hand=10, reserved=1)

    with pytest.raises(BusinessRuleViolationError, match="para enviar"):
        stock.ship(2)


def test_ajuste_corrige_o_saldo_fisico() -> None:
    stock = build_stock(on_hand=10, reserved=2)

    stock.adjust_to(8, reason="Inventario ciclico")

    assert stock.quantity_on_hand == 8
    assert stock.quantity_available == 6


def test_ajuste_abaixo_do_reservado_e_recusado() -> None:
    # Reduzir abaixo do reservado significaria ter vendido o que nao existe.
    stock = build_stock(on_hand=10, reserved=6)

    with pytest.raises(BusinessRuleViolationError, match="reservada"):
        stock.adjust_to(4, reason="Quebra")


def test_estado_inicial_inconsistente_e_recusado() -> None:
    with pytest.raises(InvariantViolationError, match="nao pode superar"):
        StockItem(uuid4(), sku="CAF-500", quantity_on_hand=2, quantity_reserved=5)


def test_movimentacoes_geram_eventos_com_o_saldo_resultante() -> None:
    stock = build_stock(on_hand=0)
    stock.receive(10)
    stock.reserve(2)

    events = stock.pull_events()

    assert [event.name for event in events] == [
        "StockMovementRecorded",
        "StockMovementRecorded",
    ]
