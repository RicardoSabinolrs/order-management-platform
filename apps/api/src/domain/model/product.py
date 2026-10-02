"""Produto do catalogo."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.exception import InvariantViolationError
from domain.model.base import AggregateRoot
from domain.model.event import DomainEvent
from domain.model.money import Money

SKU_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,31}$")
MAX_NAME_LENGTH = 120


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductCreated(DomainEvent):
    """Um produto entrou no catalogo."""

    product_id: UUID
    sku: str


class Product(AggregateRoot[UUID]):
    """Item do catalogo, identificado por um SKU unico.

    O produto conhece preco e descricao; a quantidade fisica pertence ao
    estoque (`StockItem`), que e outro agregado - assim um ajuste de preco nao
    disputa a mesma linha que uma baixa de estoque.
    """

    __slots__ = ("_active", "_created_at", "_description", "_name", "_price", "_sku", "_updated_at")

    def __init__(
        self,
        product_id: UUID,
        *,
        sku: str,
        name: str,
        description: str,
        price: Money,
        active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 0,
    ) -> None:
        super().__init__(product_id, version=version)
        self._sku = self._validate_sku(sku)
        self._name = self._validate_name(name)
        self._description = description.strip()
        self._price = price
        self._active = active
        now = datetime.now(UTC)
        self._created_at = created_at or now
        self._updated_at = updated_at or now

    # -- fabrica ------------------------------------------------------------
    @classmethod
    def create(cls, *, sku: str, name: str, description: str, price: Money) -> Product:
        """Cria um produto novo e registra o evento correspondente."""
        product = cls(uuid4(), sku=sku, name=name, description=description, price=price)
        product.record_event(ProductCreated(product_id=product.id, sku=product.sku))
        return product

    # -- validacoes ---------------------------------------------------------
    @staticmethod
    def _validate_sku(sku: str) -> str:
        normalized = sku.strip().upper()
        if not SKU_PATTERN.match(normalized):
            msg = (
                f"SKU invalido: '{sku}'. Use de 3 a 32 caracteres entre letras "
                "maiusculas, numeros e hifen."
            )
            raise InvariantViolationError(msg)
        return normalized

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            msg = "O nome do produto nao pode ser vazio."
            raise InvariantViolationError(msg)
        if len(normalized) > MAX_NAME_LENGTH:
            msg = f"O nome do produto excede {MAX_NAME_LENGTH} caracteres."
            raise InvariantViolationError(msg)
        return normalized

    # -- estado -------------------------------------------------------------
    @property
    def sku(self) -> str:
        return self._sku

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def price(self) -> Money:
        return self._price

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # -- comportamento ------------------------------------------------------
    def _touch(self) -> None:
        self._updated_at = datetime.now(UTC)

    def rename(self, name: str) -> None:
        self._name = self._validate_name(name)
        self._touch()

    def change_description(self, description: str) -> None:
        self._description = description.strip()
        self._touch()

    def change_price(self, price: Money) -> None:
        """Ajusta o preco de tabela.

        Pedidos ja criados nao sao afetados: eles guardam o preco praticado no
        momento da venda, nao uma referencia ao produto.
        """
        self._price = price
        self._touch()

    def activate(self) -> None:
        self._active = True
        self._touch()

    def deactivate(self) -> None:
        """Retira o produto de circulacao.

        Desativar preserva o historico; excluir quebraria os pedidos que o
        referenciam.
        """
        self._active = False
        self._touch()
