"""Valor monetario."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from domain.exception import InvariantViolationError
from domain.model.base import ValueObject

DEFAULT_CURRENCY = "BRL"
CURRENCY_CODE_LENGTH = 3  # ISO-4217


@dataclass(frozen=True, slots=True)
class Money(ValueObject):
    """Quantia em centavos.

    Dinheiro nunca e representado em ponto flutuante: `0.1 + 0.2 != 0.3` em
    binario, e um centavo perdido por arredondamento vira divergencia contabil.
    """

    amount_in_cents: int
    currency: str = DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        if self.amount_in_cents < 0:
            msg = "Valor monetario nao pode ser negativo."
            raise InvariantViolationError(msg)
        if len(self.currency) != CURRENCY_CODE_LENGTH or not self.currency.isalpha():
            msg = f"Moeda invalida: '{self.currency}'. Use o codigo ISO-4217 (ex.: BRL)."
            raise InvariantViolationError(msg)

    @classmethod
    def zero(cls, currency: str = DEFAULT_CURRENCY) -> Self:
        return cls(0, currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            msg = f"Nao e possivel operar {self.currency} com {other.currency}."
            raise InvariantViolationError(msg)

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount_in_cents + other.amount_in_cents, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount_in_cents - other.amount_in_cents, self.currency)

    def multiply(self, factor: int) -> Money:
        """Multiplica por uma quantidade inteira (sem risco de arredondamento)."""
        if factor < 0:
            msg = "Fator de multiplicacao nao pode ser negativo."
            raise InvariantViolationError(msg)
        return Money(self.amount_in_cents * factor, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount_in_cents / 100:.2f}"
