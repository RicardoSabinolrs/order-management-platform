"""Pedido de venda."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from domain.exception import BusinessRuleViolationError, InvariantViolationError
from domain.model.base import AggregateRoot, ValueObject
from domain.model.event import DomainEvent
from domain.model.money import Money

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# A maquina de estados explicita: qualquer transicao fora deste mapa e recusada.
# Deixar isso implicito em `if`s espalhados e como pedidos entregues voltam a
# "pendente" em producao.
ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class InvalidStatusTransitionError(BusinessRuleViolationError):
    """A transicao pedida nao existe na maquina de estados."""

    code = "invalid_status_transition"

    def __init__(self, *, current: OrderStatus, target: OrderStatus) -> None:
        allowed = sorted(status.value for status in ALLOWED_TRANSITIONS[current])
        super().__init__(
            f"Um pedido '{current.value}' nao pode ir para '{target.value}'. "
            f"Transicoes possiveis: {', '.join(allowed) or 'nenhuma'}."
        )
        self.current = current
        self.target = target

    def details(self) -> dict[str, object]:
        return {
            "current_status": self.current.value,
            "target_status": self.target.value,
            "allowed": sorted(status.value for status in ALLOWED_TRANSITIONS[self.current]),
        }


@dataclass(frozen=True, slots=True)
class Customer(ValueObject):
    """Dados do comprador, copiados no pedido."""

    name: str
    email: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "O nome do cliente nao pode ser vazio."
            raise InvariantViolationError(msg)
        if not EMAIL_PATTERN.match(self.email):
            msg = f"E-mail invalido: '{self.email}'."
            raise InvariantViolationError(msg)


@dataclass(frozen=True, slots=True)
class OrderItem(ValueObject):
    """Linha do pedido.

    SKU, descricao e preco sao copiados do produto no momento da venda. Se o
    catalogo mudar depois, o pedido continua refletindo o que foi combinado.
    """

    product_id: UUID
    sku: str
    description: str
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            msg = "A quantidade do item precisa ser maior que zero."
            raise InvariantViolationError(msg)

    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderPlaced(DomainEvent):
    order_id: UUID
    reference: str
    total_in_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderStatusChanged(DomainEvent):
    order_id: UUID
    previous: OrderStatus
    current: OrderStatus


class Order(AggregateRoot[UUID]):
    """Pedido de venda: a fronteira transacional das suas proprias linhas."""

    __slots__ = (
        "_cancellation_reason",
        "_customer",
        "_items",
        "_placed_at",
        "_reference",
        "_status",
        "_updated_at",
    )

    def __init__(
        self,
        order_id: UUID,
        *,
        reference: str,
        customer: Customer,
        items: list[OrderItem],
        status: OrderStatus = OrderStatus.PENDING,
        placed_at: datetime | None = None,
        updated_at: datetime | None = None,
        cancellation_reason: str | None = None,
        version: int = 0,
    ) -> None:
        super().__init__(order_id, version=version)
        if not items:
            msg = "Um pedido precisa de pelo menos um item."
            raise InvariantViolationError(msg)

        self._reference = reference
        self._customer = customer
        self._items = list(items)
        self._status = status
        self._cancellation_reason = cancellation_reason
        now = datetime.now(UTC)
        self._placed_at = placed_at or now
        self._updated_at = updated_at or now

    @classmethod
    def place(cls, *, reference: str, customer: Customer, items: list[OrderItem]) -> Order:
        """Registra um pedido novo."""
        order = cls(uuid4(), reference=reference, customer=customer, items=items)
        order.record_event(
            OrderPlaced(
                order_id=order.id,
                reference=order.reference,
                total_in_cents=order.total.amount_in_cents,
            )
        )
        return order

    # -- estado -------------------------------------------------------------
    @property
    def reference(self) -> str:
        return self._reference

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def items(self) -> tuple[OrderItem, ...]:
        """Copia imutavel: alterar itens so pelos metodos do agregado."""
        return tuple(self._items)

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def cancellation_reason(self) -> str | None:
        return self._cancellation_reason

    @property
    def placed_at(self) -> datetime:
        return self._placed_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def total(self) -> Money:
        total = Money.zero(self._items[0].unit_price.currency)
        for item in self._items:
            total = total + item.subtotal
        return total

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self._items)

    @property
    def is_editable(self) -> bool:
        """Itens so mudam antes da confirmacao: depois dela o estoque ja foi comprometido."""
        return self._status is OrderStatus.PENDING

    # -- edicao -------------------------------------------------------------
    def _require_editable(self) -> None:
        if not self.is_editable:
            msg = (
                f"Os itens de um pedido '{self._status.value}' nao podem ser alterados. "
                "Somente pedidos pendentes sao editaveis."
            )
            raise BusinessRuleViolationError(msg)

    def _touch(self) -> None:
        self._updated_at = datetime.now(UTC)

    def change_customer(self, customer: Customer) -> None:
        self._require_editable()
        self._customer = customer
        self._touch()

    def replace_items(self, items: list[OrderItem]) -> None:
        """Substitui todas as linhas do pedido."""
        self._require_editable()
        if not items:
            msg = "Um pedido precisa de pelo menos um item."
            raise InvariantViolationError(msg)
        self._items = list(items)
        self._touch()

    # -- maquina de estados -------------------------------------------------
    def _transition_to(self, target: OrderStatus) -> None:
        if target not in ALLOWED_TRANSITIONS[self._status]:
            raise InvalidStatusTransitionError(current=self._status, target=target)

        previous = self._status
        self._status = target
        self._touch()
        self.record_event(OrderStatusChanged(order_id=self.id, previous=previous, current=target))

    def confirm(self) -> None:
        """Confirma o pedido. O estoque reservado passa a ser compromisso firme."""
        self._transition_to(OrderStatus.CONFIRMED)

    def ship(self) -> None:
        """Marca o envio. A partir daqui a mercadoria saiu do deposito."""
        self._transition_to(OrderStatus.SHIPPED)

    def deliver(self) -> None:
        """Conclui o pedido."""
        self._transition_to(OrderStatus.DELIVERED)

    def cancel(self, reason: str) -> None:
        """Cancela o pedido e libera o que estava reservado."""
        if not reason.strip():
            msg = "Informe o motivo do cancelamento."
            raise InvariantViolationError(msg)
        self._transition_to(OrderStatus.CANCELLED)
        self._cancellation_reason = reason.strip()
