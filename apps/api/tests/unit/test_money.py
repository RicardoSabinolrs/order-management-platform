"""Value object monetario."""

from __future__ import annotations

import pytest

from domain.exception import InvariantViolationError
from domain.model.money import Money


def test_soma_preserva_a_moeda() -> None:
    assert Money(1000) + Money(500) == Money(1500, "BRL")


def test_multiplicacao_por_quantidade_inteira() -> None:
    assert Money(3290).multiply(3) == Money(9870)


def test_nao_permite_valor_negativo() -> None:
    with pytest.raises(InvariantViolationError, match="negativo"):
        Money(-1)


def test_subtracao_abaixo_de_zero_e_recusada() -> None:
    with pytest.raises(InvariantViolationError, match="negativo"):
        Money(100) - Money(101)


def test_nao_mistura_moedas() -> None:
    with pytest.raises(InvariantViolationError, match="BRL com USD"):
        Money(100, "BRL") + Money(100, "USD")


def test_recusa_codigo_de_moeda_invalido() -> None:
    with pytest.raises(InvariantViolationError, match="Moeda invalida"):
        Money(100, "REAL")


def test_igualdade_e_estrutural() -> None:
    assert Money(500, "BRL") == Money(500, "BRL")
    assert Money(500, "BRL") != Money(500, "USD")
