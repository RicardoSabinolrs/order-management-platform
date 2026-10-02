"""Regras do catalogo de produtos."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from domain.exception import BusinessRuleViolationError, EntityNotFoundError
from domain.model.money import Money
from domain.model.product import Product
from domain.model.stock import StockItem
from domain.repository.base import UnitOfWork
from domain.repository.product import ProductFilter
from domain.schema.page import Page, PageQuery
from domain.schema.product import ProductCreate, ProductRead, ProductUpdate


class DuplicateSkuError(BusinessRuleViolationError):
    """Ja existe um produto com o SKU informado."""

    code = "duplicate_sku"


class ProductService:
    """CRUD do catalogo.

    Cada operacao abre a sua propria transacao: um caso de uso, uma unidade de
    trabalho.
    """

    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work_factory

    async def create(self, payload: ProductCreate) -> ProductRead:
        """Cadastra um produto e cria o registro de estoque correspondente.

        Produto e estoque nascem juntos: sem o registro de saldo, a primeira
        venda encontraria um estoque inexistente em vez de saldo zero.
        """
        async with self._unit_of_work() as uow:
            sku = payload.sku.strip().upper()
            if await uow.products.get_by_sku(sku) is not None:
                msg = f"Ja existe um produto com o SKU {sku}."
                raise DuplicateSkuError(msg)

            product = Product.create(
                sku=sku,
                name=payload.name,
                description=payload.description,
                price=Money(payload.price_in_cents, payload.currency.upper()),
            )
            await uow.products.add(product)

            stock = StockItem(product.id, sku=product.sku)
            if payload.initial_stock > 0:
                stock.receive(payload.initial_stock)
            await uow.stock.add(stock)

            await uow.commit()
            return ProductRead.from_domain(product)

    async def get(self, product_id: UUID) -> ProductRead:
        async with self._unit_of_work() as uow:
            return ProductRead.from_domain(await self._require(uow, product_id))

    async def paginate(
        self,
        *,
        page_query: PageQuery,
        search: str | None = None,
        active: bool | None = None,
    ) -> Page[ProductRead]:
        async with self._unit_of_work() as uow:
            products, total = await uow.products.paginate(
                filters=ProductFilter(search=search, active=active),
                offset=page_query.offset,
                limit=page_query.page_size,
            )
            return Page[ProductRead](
                items=[ProductRead.from_domain(product) for product in products],
                total=total,
                page=page_query.page,
                page_size=page_query.page_size,
            )

    async def update(self, product_id: UUID, payload: ProductUpdate) -> ProductRead:
        """Aplica uma alteracao parcial. Campos ausentes ficam como estao."""
        async with self._unit_of_work() as uow:
            product = await self._require(uow, product_id)

            if payload.name is not None:
                product.rename(payload.name)
            if payload.description is not None:
                product.change_description(payload.description)
            if payload.price_in_cents is not None:
                product.change_price(Money(payload.price_in_cents, product.price.currency))
            if payload.active is not None:
                product.activate() if payload.active else product.deactivate()

            await uow.products.save(product)
            await uow.commit()
            return ProductRead.from_domain(product)

    async def delete(self, product_id: UUID) -> None:
        """Remove o produto do catalogo.

        So e permitido enquanto nao houver estoque reservado: excluir algo
        prometido a um pedido deixaria o pedido orfao.
        """
        async with self._unit_of_work() as uow:
            product = await self._require(uow, product_id)

            stock = await uow.stock.get(product_id)
            if stock is not None and stock.quantity_reserved > 0:
                msg = (
                    f"O produto {product.sku} tem {stock.quantity_reserved} unidade(s) "
                    "reservada(s) em pedidos. Desative-o em vez de excluir."
                )
                raise BusinessRuleViolationError(msg)

            await uow.products.delete(product)
            await uow.commit()

    @staticmethod
    async def _require(uow: UnitOfWork, product_id: UUID) -> Product:
        product = await uow.products.get(product_id)
        if product is None:
            msg = f"Produto {product_id} nao encontrado."
            raise EntityNotFoundError(msg)
        return product
