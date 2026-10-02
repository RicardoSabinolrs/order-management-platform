"""Controle de estoque."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from domain.exception import BusinessRuleViolationError, InvariantViolationError
from domain.model.base import AggregateRoot
from domain.model.event import DomainEvent


class InsufficientStockError(BusinessRuleViolationError):
    """Nao ha saldo disponivel para atender a reserva."""

    code = "insufficient_stock"

    def __init__(self, *, sku: str, requested: int, available: int) -> None:
        super().__init__(
            f"Estoque insuficiente para o SKU {sku}: "
            f"solicitado {requested}, disponivel {available}."
        )
        self.sku = sku
        self.requested = requested
        self.available = available

    def details(self) -> dict[str, object]:
        return {"sku": self.sku, "requested": self.requested, "available": self.available}


class StockMovementKind(StrEnum):
    """Por que o saldo mudou. O historico depende disso para auditoria."""

    RECEIPT = "receipt"
    RESERVATION = "reservation"
    RELEASE = "release"
    SHIPMENT = "shipment"
    ADJUSTMENT = "adjustment"


@dataclass(frozen=True, slots=True, kw_only=True)
class StockMovementRecorded(DomainEvent):
    """Uma movimentacao de estoque foi efetivada."""

    product_id: UUID
    kind: StockMovementKind
    quantity: int
    quantity_on_hand: int


class StockItem(AggregateRoot[UUID]):
    """Saldo de um produto.

    A identidade do agregado e o proprio `product_id`: existe exatamente um
    registro de estoque por produto.

    Dois saldos sao mantidos separados:

    - `quantity_on_hand`   o que existe fisicamente no deposito;
    - `quantity_reserved`  o que ja foi prometido a pedidos ainda nao enviados.

    O que pode ser vendido e a diferenca entre os dois. Sem essa separacao,
    dois pedidos simultaneos venderiam a mesma peca.
    """

    __slots__ = ("_quantity_on_hand", "_quantity_reserved", "_sku", "_updated_at")

    def __init__(
        self,
        product_id: UUID,
        *,
        sku: str,
        quantity_on_hand: int = 0,
        quantity_reserved: int = 0,
        updated_at: datetime | None = None,
        version: int = 0,
    ) -> None:
        super().__init__(product_id, version=version)
        if quantity_on_hand < 0 or quantity_reserved < 0:
            msg = "Saldo de estoque nao pode ser negativo."
            raise InvariantViolationError(msg)
        if quantity_reserved > quantity_on_hand:
            msg = "A quantidade reservada nao pode superar a quantidade em maos."
            raise InvariantViolationError(msg)

        self._sku = sku
        self._quantity_on_hand = quantity_on_hand
        self._quantity_reserved = quantity_reserved
        self._updated_at = updated_at or datetime.now(UTC)

    @property
    def product_id(self) -> UUID:
        return self.id

    @property
    def sku(self) -> str:
        return self._sku

    @property
    def quantity_on_hand(self) -> int:
        return self._quantity_on_hand

    @property
    def quantity_reserved(self) -> int:
        return self._quantity_reserved

    @property
    def quantity_available(self) -> int:
        """Saldo que ainda pode ser vendido."""
        return self._quantity_on_hand - self._quantity_reserved

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @staticmethod
    def _require_positive(quantity: int) -> int:
        if quantity <= 0:
            msg = "A quantidade movimentada precisa ser maior que zero."
            raise InvariantViolationError(msg)
        return quantity

    def _record(self, kind: StockMovementKind, quantity: int) -> None:
        self._updated_at = datetime.now(UTC)
        self.record_event(
            StockMovementRecorded(
                product_id=self.id,
                kind=kind,
                quantity=quantity,
                quantity_on_hand=self._quantity_on_hand,
            )
        )

    # -- entradas -----------------------------------------------------------
    def receive(self, quantity: int) -> None:
        """Entrada de mercadoria no deposito."""
        self._quantity_on_hand += self._require_positive(quantity)
        self._record(StockMovementKind.RECEIPT, quantity)

    def adjust_to(self, quantity_on_hand: int, *, reason: str) -> None:
        """Corrige o saldo fisico apos inventario.

        Nao permite deixar o saldo abaixo do que ja esta reservado: isso
        significaria ter vendido mercadoria que nao existe.
        """
        if quantity_on_hand < 0:
            msg = "O saldo ajustado nao pode ser negativo."
            raise InvariantViolationError(msg)
        if quantity_on_hand < self._quantity_reserved:
            msg = (
                f"Ajuste recusado: ha {self._quantity_reserved} unidade(s) reservada(s) "
                f"do SKU {self._sku}. Cancele os pedidos antes de reduzir o saldo. "
                f"Motivo informado: {reason}."
            )
            raise BusinessRuleViolationError(msg)

        delta = quantity_on_hand - self._quantity_on_hand
        self._quantity_on_hand = quantity_on_hand
        self._record(StockMovementKind.ADJUSTMENT, delta)

    # -- reservas -----------------------------------------------------------
    def reserve(self, quantity: int) -> None:
        """Promete mercadoria a um pedido."""
        self._require_positive(quantity)
        if quantity > self.quantity_available:
            raise InsufficientStockError(
                sku=self._sku,
                requested=quantity,
                available=self.quantity_available,
            )
        self._quantity_reserved += quantity
        self._record(StockMovementKind.RESERVATION, quantity)

    def release(self, quantity: int) -> None:
        """Devolve ao disponivel o que havia sido reservado (pedido cancelado)."""
        self._require_positive(quantity)
        if quantity > self._quantity_reserved:
            msg = f"Nao ha {quantity} unidade(s) reservada(s) do SKU {self._sku} para liberar."
            raise BusinessRuleViolationError(msg)
        self._quantity_reserved -= quantity
        self._record(StockMovementKind.RELEASE, quantity)

    def ship(self, quantity: int) -> None:
        """Baixa definitiva: a mercadoria reservada saiu do deposito."""
        self._require_positive(quantity)
        if quantity > self._quantity_reserved:
            msg = f"Nao ha {quantity} unidade(s) reservada(s) do SKU {self._sku} para enviar."
            raise BusinessRuleViolationError(msg)
        self._quantity_reserved -= quantity
        self._quantity_on_hand -= quantity
        self._record(StockMovementKind.SHIPMENT, quantity)
